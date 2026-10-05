"""
Hierarchical Network Configuration Diff Engine.
Understands Cisco IOS-XE / Arista EOS / Junos block structure (e.g. interfaces, BGP blocks),
identifying additions, deletions, and modified sub-commands.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple


@dataclass
class ConfigSection:
    header: str
    lines: List[str] = field(default_factory=list)


@dataclass
class ConfigDelta:
    added_sections: List[str] = field(default_factory=list)
    removed_sections: List[str] = field(default_factory=list)
    modified_sections: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)
    # modified_sections: section_header -> {"added": [...], "removed": [...]}


class NetworkConfigDiffer:
    """Parses hierarchical network device configurations and produces structured deltas."""

    @classmethod
    def _parse_sections(cls, config_text: str) -> Dict[str, List[str]]:
        """Parse indented configuration into a dict: header -> list of subcommands."""
        sections: Dict[str, List[str]] = {}
        current_section = "GLOBAL"
        sections[current_section] = []

        for line in config_text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("!") or stripped.startswith("#"):
                continue

            if line.startswith(" ") or line.startswith("\t"):
                # Subcommand inside current section
                sections[current_section].append(stripped)
            else:
                # Top-level section header
                current_section = stripped
                if current_section not in sections:
                    sections[current_section] = []

        return sections

    @classmethod
    def diff(cls, base_config: str, target_config: str) -> ConfigDelta:
        """
        Compare base (running) config vs target (intended) config.
        Returns ConfigDelta highlighting exact modifications.
        """
        base_sections = cls._parse_sections(base_config)
        target_sections = cls._parse_sections(target_config)

        delta = ConfigDelta()

        base_keys = set(base_sections.keys())
        target_keys = set(target_sections.keys())

        # Removed sections (in base but not target)
        for k in base_keys - target_keys:
            if k != "GLOBAL" or base_sections[k]:
                delta.removed_sections.append(k)

        # Added sections (in target but not base)
        for k in target_keys - base_keys:
            if k != "GLOBAL" or target_sections[k]:
                delta.added_sections.append(k)

        # Common sections - check for line diffs
        common_keys = base_keys & target_keys
        for k in common_keys:
            base_lines = set(base_sections[k])
            target_lines = set(target_sections[k])

            added_lines = sorted(list(target_lines - base_lines))
            removed_lines = sorted(list(base_lines - target_lines))

            if added_lines or removed_lines:
                delta.modified_sections[k] = {
                    "added": added_lines,
                    "removed": removed_lines
                }

        return delta
