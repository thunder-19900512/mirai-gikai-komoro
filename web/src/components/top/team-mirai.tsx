import { EXTERNAL_LINKS } from "@/config/external-links";
import { LinkButton } from "./link-button";

/**
 * 運営者についてのセクション。
 * 本家「みらい議会」ではチームみらい紹介セクションだった箇所を、
 * 小諸市版の運営者情報＋免責の明示に差し替えている。
 */
export function TeamMirai() {
  return (
    <div className="py-10">
      <div className="flex flex-col gap-6">
        {/* ヘッダー */}
        <div className="flex flex-col gap-4">
          <h2 className="text-2xl font-bold">運営について</h2>
          <p className="text-sm font-bold text-primary-accent">
            このサイトの運営者
          </p>
        </div>

        {/* コンテンツ */}
        <div className="flex flex-col gap-6">
          <div className="flex flex-col gap-3">
            <p className="text-[15px] leading-[28px] text-black">
              本サイトは、小諸市在住の山田雄司が個人として運営しています。政党チームみらいがオープンソースで公開しているプラットフォーム「みらい議会」を基に、小諸市議会の議案をわかりやすく伝えることを目指しています。
            </p>
            <p className="text-[15px] leading-[28px] text-black">
              これは政党チームみらいが運営しているものではありません。掲載内容の誤りに気づかれた方は、お気軽にご連絡ください。
            </p>
          </div>

          {/* ボタングループ */}
          <div className="flex flex-col gap-4">
            <LinkButton
              href={EXTERNAL_LINKS.HONKE_GIKAI}
              icon={{
                src: "/icons/info-icon.svg",
                alt: "",
                width: 23,
                height: 22,
              }}
            >
              本家「みらい議会」（国会版）を見る
            </LinkButton>

            <LinkButton
              href={EXTERNAL_LINKS.REPORT}
              icon={{
                src: "/icons/report-error.svg",
                alt: "",
                width: 20,
                height: 20,
              }}
            >
              誤り・不具合を報告する
            </LinkButton>
          </div>
        </div>
      </div>
    </div>
  );
}
