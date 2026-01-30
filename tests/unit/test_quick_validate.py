"""
Unit tests for quick_validate.py - YAML-like frontmatter parsing.

Tests validate the _parse_frontmatter_simple() function with focus on
multiline string handling (|- marker) with proper indent processing.
"""

from pathlib import Path


# Import the function to test
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".github" / "skills" / "skill-creator" / "scripts"))

from quick_validate import _parse_frontmatter_simple


class TestParseMultilineIndent:
    """Test multiline value parsing with YAML-spec indent handling."""

    def test_正常系_基本的なマルチラインで基準インデントが除去される(self) -> None:
        """基本的なマルチライン値で、最初の非空行のインデントが基準として除去される。

        前提条件:
            - SKILL.mdフロントマター内に|- で始まるマルチライン値
            - 複数行が同一インデントレベルで配置されている

        期待結果:
            - 最初の非空行のインデントレベルを基準として除去される
            - 各行の相対インデントは保持される
        """
        content = """---
description: |-
  This is a description
  with multiple lines
  properly indented
---

# Content after"""

        result = _parse_frontmatter_simple(content)

        # YAML仕様では、最初の非空行のインデント（2スペース）が基準
        # 各行からそのインデントを除去すると：
        # "This is a description\nwith multiple lines\nproperly indented"
        expected = "This is a description\nwith multiple lines\nproperly indented"
        assert result is not None
        assert result["description"] == expected

    def test_異常系_インデント処理で異なるレベルのインデント保持(self) -> None:
        """マルチライン内で異なるインデントレベルがある場合、基準より深いインデントは保持される。

        前提条件:
            - 最初の非空行のインデント：2スペース
            - 2行目以降：4スペース（基準より2スペース深い）

        期待結果:
            - 基準インデント（2スペース）は除去
            - 相対インデント（+2スペース）は保持される
        """
        content = """---
description: |-
  Base level
    Indented more
  Back to base
---

# Content"""

        result = _parse_frontmatter_simple(content)

        # 基準インデント（2スペース）を除去し、相対インデント（2スペース）は保持
        expected = "Base level\n  Indented more\nBack to base"
        assert result is not None
        assert result["description"] == expected

    def test_エッジケース_トレーリング空行が削除される(self) -> None:
        """マルチライン末尾の空行が適切に削除される。

        前提条件:
            - マルチラインの末尾に空行が複数存在

        期待結果:
            - トレーリング空行がすべて削除される
            - 内容部分は保持される
        """
        content = """---
description: |-
  Content here
  Another line

---

# Content"""

        result = _parse_frontmatter_simple(content)

        # トレーリング空行は除去される
        expected = "Content here\nAnother line"
        assert result is not None
        assert result["description"] == expected

    def test_正常系_複数のマルチラインキーが正しく処理される(self) -> None:
        """複数のマルチラインキーが同一フロントマター内で正しく処理される。

        前提条件:
            - 複数のマルチライン値が存在
            - 各々異なるインデント特性を持つ

        期待結果:
            - 各マルチラインが独立してインデント処理される
        """
        content = """---
description: |-
  First description
  with content
name: test-skill
metadata: |-
  Second metadata
    with nested indent
---

# Content"""

        result = _parse_frontmatter_simple(content)

        assert result is not None
        # description
        expected_desc = "First description\nwith content"
        assert result["description"] == expected_desc
        # name
        assert result["name"] == "test-skill"
        # metadata with nested indent
        expected_meta = "Second metadata\n  with nested indent"
        assert result["metadata"] == expected_meta


class TestParseFrontmatterBasics:
    """Test basic frontmatter parsing (non-multiline cases)."""

    def test_正常系_単純な文字列値が解析される(self) -> None:
        """単純な key: value 形式が正しく解析される。"""
        content = """---
name: test-skill
description: Simple description
---

# Content"""

        result = _parse_frontmatter_simple(content)

        assert result is not None
        assert result["name"] == "test-skill"
        assert result["description"] == "Simple description"

    def test_正常系_クォート付き値が正しく処理される(self) -> None:
        """ダブルクォートで囲まれた値が正しく処理される。"""
        content = """---
name: "quoted-value"
---

# Content"""

        result = _parse_frontmatter_simple(content)

        assert result is not None
        assert result["name"] == "quoted-value"

    def test_異常系_フロントマターがない場合None(self) -> None:
        """フロントマターがない内容ではNoneが返される。"""
        content = "# No frontmatter here\nJust content"

        result = _parse_frontmatter_simple(content)

        assert result is None

    def test_異常系_不正な形式ではNone(self) -> None:
        """閉じていないフロントマターは None が返される。"""
        content = """---
name: test-skill

# No closing ---
"""

        result = _parse_frontmatter_simple(content)

        assert result is None
