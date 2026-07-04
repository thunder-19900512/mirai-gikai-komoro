/**
 * 外部リンク定数
 *
 * 本フォーク（みらい議会＠小諸市）では、本家チームみらいのリンクを
 * 小諸市版の運営情報・出典リンクに差し替えている。
 */
export const EXTERNAL_LINKS = {
  /** 不具合・誤り報告先（当面はメール） */
  REPORT: "mailto:thunder.ymd@gmail.com?subject=みらい議会＠小諸市への報告",
  /** このサイトについて（ソースコード・運営情報） */
  ABOUT_NOTE: "https://github.com/thunder-19900512/mirai-gikai-komoro",
  /** 本家「みらい議会」（チームみらい運営） */
  HONKE_GIKAI: "https://gikai.team-mir.ai/",
  /** 小諸市議会 公式サイト */
  KOMORO_GIKAI:
    "https://www.city.komoro.lg.jp/official/shisei_machizukuri/komoroshigikai/index.html",
  /** よくあるご質問（リポジトリのREADME） */
  FAQ: "https://github.com/thunder-19900512/mirai-gikai-komoro#readme",
} as const;
