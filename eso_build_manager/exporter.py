"""Build export / import — internal JSON format and plain-text summary."""
import json

import eso_build_manager.storage.database as db
from eso_build_manager.models.build import Build

_VERSION = 1


def export_build_dict(build_id: int) -> dict:
    build = db.get_build(build_id)
    if build is None:
        raise ValueError(f"Build {build_id} not found")
    skills = db.get_skills(build_id)
    gear = db.get_gear(build_id)

    return {
        "_eso_build_manager_version": _VERSION,
        "name": build.name,
        "eso_class": build.eso_class,
        "subclass_1": build.subclass_1,
        "subclass_2": build.subclass_2,
        "role": build.role,
        "content": build.content,
        "game_patch": build.game_patch,
        "source": build.source,
        "mundus_stone": build.mundus_stone,
        "food_buff": build.food_buff,
        "attribute_health": build.attribute_health,
        "attribute_magicka": build.attribute_magicka,
        "attribute_stamina": build.attribute_stamina,
        "champion_points": build.champion_points,
        "cp_slots": json.loads(build.cp_slots) if build.cp_slots else [],
        "class_masteries": build.class_masteries,
        "notes": build.notes,
        "skills": [
            {"bar": s.bar, "slot": s.slot, "name": s.name}
            for s in skills if s.name.strip()
        ],
        "gear": [
            {
                "slot": g.slot,
                "set_name": g.set_name,
                "weight": g.weight,
                "trait": g.trait,
                "enchant": g.enchant,
                "quality": g.quality,
            }
            for g in gear
        ],
    }


def import_build_dict(data: dict) -> int:
    """Create a new build from an exported dict. Returns the new build_id."""
    build = Build(
        name=data.get("name", "Imported Build"),
        eso_class=data.get("eso_class", ""),
        subclass_1=data.get("subclass_1", ""),
        subclass_2=data.get("subclass_2", ""),
        role=data.get("role", ""),
        content=data.get("content", ""),
        game_patch=data.get("game_patch", "U50"),
        source=data.get("source", ""),
        mundus_stone=data.get("mundus_stone", ""),
        food_buff=data.get("food_buff", ""),
        attribute_health=data.get("attribute_health", 0),
        attribute_magicka=data.get("attribute_magicka", 0),
        attribute_stamina=data.get("attribute_stamina", 64),
        champion_points=data.get("champion_points", ""),
        cp_slots=json.dumps(data.get("cp_slots", [])),
        class_masteries=data.get("class_masteries", ""),
        notes=data.get("notes", ""),
    )
    build_id = db.create_build(build)

    from eso_build_manager.models.skill import Skill
    from eso_build_manager.models.gear import GearPiece

    skills = [
        Skill(build_id=build_id, bar=s["bar"], slot=s["slot"], name=s["name"])
        for s in data.get("skills", [])
    ]
    db.save_skills(build_id, skills)

    gear = [
        GearPiece(
            build_id=build_id,
            slot=g["slot"],
            set_name=g.get("set_name", ""),
            weight=g.get("weight", ""),
            trait=g.get("trait", ""),
            enchant=g.get("enchant", ""),
            quality=g.get("quality", "Epic"),
        )
        for g in data.get("gear", [])
    ]
    if gear:
        db.save_gear(build_id, gear)

    return build_id


def export_build_text(build_id: int) -> str:
    build = db.get_build(build_id)
    if build is None:
        return ""
    skills = db.get_skills(build_id)
    gear = db.get_gear(build_id)

    lines: list[str] = []

    # ── Header ────────────────────────────────────────────────────────────
    lines.append("=" * 52)
    lines.append(f"  {build.name}")
    tags = [t for t in [build.eso_class, build.role, build.content, build.game_patch] if t]
    if build.subclass_1:
        tags.insert(1, f"({build.subclass_1}" + (f" / {build.subclass_2}" if build.subclass_2 else "") + ")")
    if tags:
        lines.append("  " + "  ·  ".join(tags))
    lines.append("=" * 52)
    lines.append("")

    # ── Skills ────────────────────────────────────────────────────────────
    by_slot = {(s.bar, s.slot): s.name for s in skills}
    lines.append("SKILLS")
    for bar_idx, bar_label in [(0, "Front Bar"), (1, "Back Bar ")]:
        actives = "  ·  ".join(by_slot.get((bar_idx, i), "—") for i in range(5))
        ult = by_slot.get((bar_idx, 5), "—")
        lines.append(f"  {bar_label}:  {actives}  |  Ult: {ult}")
    lines.append("")

    # ── Champion Points ───────────────────────────────────────────────────
    cp_slots: list[str] = json.loads(build.cp_slots) if build.cp_slots else []
    if any(s.strip() for s in cp_slots):
        while len(cp_slots) < 12:
            cp_slots.append("")
        lines.append("CHAMPION POINTS")
        for label, start in [("Craft  ", 0), ("Warfare", 4), ("Fitness", 8)]:
            stars = ",  ".join(s or "—" for s in cp_slots[start:start + 4])
            lines.append(f"  {label}:  {stars}")
        lines.append("")

    # ── Gear ─────────────────────────────────────────────────────────────
    lines.append("GEAR")
    gear_by_slot = {g.slot: g for g in gear}
    from eso_build_manager.constants import GEAR_SLOTS
    for slot in GEAR_SLOTS:
        piece = gear_by_slot.get(slot)
        if piece and piece.weight == "N/A":
            lines.append(f"  {slot:<14}  N/A")
        elif piece and piece.set_name.strip():
            parts = [piece.set_name]
            for v in [piece.weight, piece.trait, piece.enchant, piece.quality]:
                if v and v not in ("", "—"):
                    parts.append(v)
            lines.append(f"  {slot:<14}  " + "  ·  ".join(parts))
        else:
            lines.append(f"  {slot:<14}  —")
    lines.append("")

    # ── Stats & Buffs ─────────────────────────────────────────────────────
    lines.append("STATS & BUFFS")
    lines.append(
        f"  Health: {build.attribute_health} pts  |  "
        f"Magicka: {build.attribute_magicka} pts  |  "
        f"Stamina: {build.attribute_stamina} pts"
    )
    if build.food_buff:
        lines.append(f"  Food:    {build.food_buff}")
    if build.mundus_stone:
        lines.append(f"  Mundus:  {build.mundus_stone}")
    lines.append("")

    # ── Notes ─────────────────────────────────────────────────────────────
    if build.notes.strip():
        lines.append("NOTES")
        for note_line in build.notes.strip().splitlines():
            lines.append(f"  {note_line}")
        lines.append("")

    # ── Source ────────────────────────────────────────────────────────────
    if build.source.strip():
        lines.append(f"Source: {build.source.strip()}")

    return "\n".join(lines)
