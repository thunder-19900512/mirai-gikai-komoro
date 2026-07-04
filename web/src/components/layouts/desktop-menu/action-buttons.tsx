import { LinkButton } from "@/components/top/link-button";
import { EXTERNAL_LINKS } from "@/config/external-links";

/**
 * デスクトップメニュー: アクションボタン（サイドバー内）
 */
export function DesktopMenuActionButtons() {
  return (
    <div className="flex flex-col gap-3">
      <LinkButton
        href={EXTERNAL_LINKS.ABOUT_NOTE}
        icon={{
          src: "/icons/info-icon.svg",
          alt: "",
          width: 20,
          height: 20,
        }}
      >
        このサイトについて
      </LinkButton>

      <LinkButton
        href={EXTERNAL_LINKS.HONKE_GIKAI}
        icon={{
          src: "/icons/info-icon.svg",
          alt: "本家みらい議会",
          width: 20,
          height: 20,
        }}
      >
        本家「みらい議会」
      </LinkButton>
    </div>
  );
}
