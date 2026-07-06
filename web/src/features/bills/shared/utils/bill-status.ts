import type { BillStatusEnum } from "../types";

/**
 * 小諸市版フォークの追加: 一般質問かどうかの判定。
 * 一般質問は議決（可決/否決）を持たないため、status_note の先頭マーカーで見分け、
 * 議決前提のステータス表示（バッジ・審議バー）を出さないようにする。
 * インポーター(komoro/import-session.ts)が kind="一般質問" のとき status_note を
 * 「一般質問（…」で始める規約に依存する。
 */
export function isGeneralQuestion(statusNote?: string | null): boolean {
  return !!statusNote && statusNote.startsWith("一般質問");
}

/** カード用の簡略化されたステータスラベルを取得 */
export function getCardStatusLabel(status: BillStatusEnum): string {
  switch (status) {
    case "introduced":
    case "in_originating_house":
    case "in_receiving_house":
      return "市議会審議中";
    case "enacted":
      return "可決";
    case "rejected":
      return "否決";
    default:
      return "提出前";
  }
}

/** ステータスに対応するBadgeのvariantを取得 */
export function getStatusVariant(
  status: BillStatusEnum
): "light" | "default" | "dark" | "muted" {
  switch (status) {
    case "introduced":
    case "in_originating_house":
    case "in_receiving_house":
      return "light";
    case "enacted":
      return "default";
    case "rejected":
      return "dark";
    default:
      return "muted";
  }
}
