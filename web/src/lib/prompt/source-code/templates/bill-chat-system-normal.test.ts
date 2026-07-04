import { describe, expect, it } from "vitest";
import { buildBillChatSystemNormalPrompt } from "./bill-chat-system-normal";

describe("buildBillChatSystemNormalPrompt", () => {
  it("4つのパラメータがプロンプトに埋め込まれる", () => {
    const result = buildBillChatSystemNormalPrompt(
      "テスト議案名",
      "テスト議案タイトル",
      "テスト議案要約",
      "テスト議案詳細"
    );

    expect(result).toContain("テスト議案名");
    expect(result).toContain("テスト議案タイトル");
    expect(result).toContain("テスト議案要約");
    expect(result).toContain("テスト議案詳細");
  });

  it("難易度「ふつう」セクションが含まれる", () => {
    const result = buildBillChatSystemNormalPrompt("a", "b", "c", "d");

    expect(result).toContain("回答の難易度：ふつう");
  });

  it("みらい議会の説明が含まれる", () => {
    const result = buildBillChatSystemNormalPrompt("a", "b", "c", "d");

    expect(result).toContain("みらい議会");
    expect(result).toContain("チームみらい");
  });

  it("knowledgeSource を渡すと <knowledge_source> セクションが含まれる", () => {
    const result = buildBillChatSystemNormalPrompt(
      "a",
      "b",
      "c",
      "d",
      "補足知識"
    );

    expect(result).toContain("補足ナレッジ");
    expect(result).toContain("補足知識");
  });

  it("knowledgeSource を省略するとセクションごと出ない", () => {
    const result = buildBillChatSystemNormalPrompt("a", "b", "c", "d");

    expect(result).not.toContain("<knowledge_source>");
  });
});
