/**
 * みらい議会＠小諸市：定例会の議案データ（JSON）をローカル/本番のSupabaseへ投入するインポーター。
 *
 * - 会期(diet_sessions)を upsert（slug 一意）
 * - 議案(bills)を upsert（slug=`${session.slug}-${議案番号スラッグ}` 一意）
 * - 難易度別コンテンツ(bill_contents: normal / hard)を upsert
 *
 * すべて publish_status = 'draft'（非公開）で投入する。公開は admin 画面で人間が
 * 原典照合のうえ行う前提（公選法配慮・ハルシネーション対策）。
 *
 * 使い方:
 *   dotenv -e .env -- npx tsx komoro/import-session.ts komoro/data/reiwa7-09.json
 *
 * 必須env: SUPABASE_URL, SUPABASE_SECRET_KEY
 */
import { readFileSync } from "node:fs";
import { createClient } from "@supabase/supabase-js";

type Difficulty = { title: string; summary: string; content: string };
type BillInput = {
  bill_number: string;
  name: string;
  committee: string;
  result: string;
  status: "preparing" | "introduced" | "in_originating_house" | "in_receiving_house" | "enacted" | "rejected";
  is_featured?: boolean;
  normal: Difficulty;
  hard: Difficulty;
};
type SessionFile = {
  session: { name: string; slug: string; start_date: string; end_date: string; source_url?: string };
  bills: BillInput[];
};

function requireEnv(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`Missing required environment variable: ${name}`);
  return v;
}

/** 議案番号（例: 議案第104号 / 発議第6号）を URL 用スラッグに変換 */
function billNumberSlug(billNumber: string): string {
  const map: Record<string, string> = { "議案第": "gian-", "発議第": "hatsugi-", "諮問第": "shimon-", "諸報第": "shoho-" };
  let s = billNumber;
  for (const [k, v] of Object.entries(map)) s = s.replace(k, v);
  return s.replace("号", "").trim();
}

async function main() {
  const path = process.argv[2];
  if (!path) throw new Error("Usage: tsx komoro/import-session.ts <session.json>");

  const data = JSON.parse(readFileSync(path, "utf8")) as SessionFile;
  const supabase = createClient(requireEnv("SUPABASE_URL"), requireEnv("SUPABASE_SECRET_KEY"));

  // 1) 会期 upsert
  const { data: session, error: sErr } = await supabase
    .from("diet_sessions")
    .upsert(
      {
        name: data.session.name,
        slug: data.session.slug,
        start_date: data.session.start_date,
        end_date: data.session.end_date,
        shugiin_url: data.session.source_url ?? null,
        is_active: false,
      },
      { onConflict: "slug" }
    )
    .select()
    .single();
  if (sErr) throw new Error(`diet_sessions upsert failed: ${sErr.message}`);
  console.log(`📅 会期: ${session.name} (${session.slug})`);

  let created = 0;
  for (const b of data.bills) {
    const slug = `${data.session.slug}-${billNumberSlug(b.bill_number)}`;
    const statusNote = `${b.bill_number}／付託: ${b.committee}／審議結果: ${b.result}（${data.session.name}）`;

    // 2) 議案 upsert（draft 固定）
    const { data: bill, error: bErr } = await supabase
      .from("bills")
      .upsert(
        {
          slug,
          name: b.name,
          // headline / description / body_markdown は本家スキーマで廃止済み。
          // 見出し・要約は bill_contents(normal/hard) 側に持つ。
          originating_house: "HR", // 市議会は単院。UIでは「小諸市議会」と表示
          status: b.status,
          status_note: statusNote,
          submitted_date: `${data.session.start_date}T00:00:00+09:00`,
          published_at: new Date().toISOString(),
          diet_session_id: session.id,
          shugiin_url: data.session.source_url ?? null, // 議案の出典（提出議案一覧）
          is_featured: b.is_featured ?? false,
          publish_status: "draft", // ← 必ず非公開。公開は人間がadminで
        },
        { onConflict: "slug" }
      )
      .select()
      .single();
    if (bErr) throw new Error(`bills upsert failed (${b.bill_number}): ${bErr.message}`);

    // 3) 難易度別コンテンツ upsert
    for (const level of ["normal", "hard"] as const) {
      const c = b[level];
      const { error: cErr } = await supabase
        .from("bill_contents")
        .upsert(
          {
            bill_id: bill.id,
            difficulty_level: level,
            title: c.title,
            summary: c.summary,
            content: c.content,
          },
          { onConflict: "bill_id,difficulty_level" }
        );
      if (cErr) throw new Error(`bill_contents upsert failed (${b.bill_number}/${level}): ${cErr.message}`);
    }
    created++;
    console.log(`  ✅ ${b.bill_number} ${b.name}  [${b.result}] draft`);
  }

  console.log(`\n🎉 ${created}件の議案を draft で投入しました（公開はadminで人間が実施）。`);
}

main().catch((e) => {
  console.error("❌", e instanceof Error ? e.message : e);
  process.exit(1);
});
