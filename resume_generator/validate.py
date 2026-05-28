"""Shared character-budget validation for one-page A4 documents."""

from dataclasses import dataclass, field


@dataclass
class Budget:
    limits: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)

    def check(self, text: str, max_chars: int, label: str) -> None:
        if len(text) > max_chars:
            self.warnings.append(
                f"[{label}] {len(text)}/{max_chars} chars: {text[:80]}..."
            )

    def report(self) -> bool:
        if self.warnings:
            print(f"\n{'='*60}")
            print(f"CHARACTER BUDGET WARNINGS ({len(self.warnings)}):")
            print(f"{'='*60}")
            for w in self.warnings:
                print(f"  {w}")
            print(f"{'='*60}\n")
            return True
        else:
            print("\nAll lines within character budget.\n")
            return False
