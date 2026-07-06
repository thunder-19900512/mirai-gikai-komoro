import { Badge } from "@/components/ui/badge";
import type { BillStatusEnum } from "../../../shared/types";
import {
  getCardStatusLabel,
  getStatusVariant,
  isGeneralQuestion,
} from "../../../shared/utils/bill-status";

interface BillStatusBadgeProps {
  status: BillStatusEnum;
  /** 一般質問判定用（議決前提のラベルを出さないため）。省略時は従来どおり議決ラベル */
  statusNote?: string | null;
  className?: string;
}

export function BillStatusBadge({
  status,
  statusNote,
  className,
}: BillStatusBadgeProps) {
  // 一般質問は議決を持たないため、中立的な「一般質問」バッジにする
  if (isGeneralQuestion(statusNote)) {
    return (
      <Badge variant="muted" className={className}>
        一般質問
      </Badge>
    );
  }
  return (
    <Badge variant={getStatusVariant(status)} className={className}>
      {getCardStatusLabel(status)}
    </Badge>
  );
}
