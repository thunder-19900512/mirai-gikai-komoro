import type { BillUpdateInput } from "../types";

/**
 * 議案のステータス変更時に、関連する公開中インタビューを自動クローズすべきかを判定する。
 * 現状は可決 (enacted) 時のみ対象。
 */
export function shouldAutoCloseInterviewOnBillStatus(
  status: BillUpdateInput["status"]
): boolean {
  return status === "enacted";
}
