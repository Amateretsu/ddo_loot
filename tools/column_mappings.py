def to_db_key(original_name):
    match original_name.lower():
        case "accepts sentience?":
            return "accepts_sentience"
        case "arcane spell failure":
            return "arcane_spell_failure"
        case "armor bonus":
            return "armor_bonus"
        case "armor check penalty":
            return "armor_check_penalty"
        case "armor type":
            return "armor_type"
        case "attack mod":
            return "attack_mod"
        case "augments":
            return "augments"
        case "base value":
            return "base_value"
        case "binding":
            return "binding"
        case "critical roll":
            return "critical_roll_and_multiplier"
        case "critical threat range":
            return "critical_roll_and_multiplier"
        case "damage":
            return "damage_and_type"
        case "damage and type":
            return "damage_and_type"
        case "damage mod":
            return "damage_mod"
        case "damage reduction":
            return "damage_reduction"
        case "description":
            return "description"
        case "durability":
            return "durability"
        case "enchantments":
            return "enchantments"
        case "enhancements":
            return "enchantments"
        case "feat requirement":
            return "feat_requirement"
        case "handedness":
            return "handedness"
        case "hardness":
            return "hardness"
        case "item type":
            return "item_type"
        case "location":
            return "location"
        case "made from":
            return "material"
        case "material":
            return "material"
        case "max dex bonus":
            return "maximum_dexterity_bonus"
        case "maximum dexterity bonus":
            return "maximum_dexterity_bonus"
        case "minimum level":
            return "minimum_level"
        case "mythic bonus":
            return "mythic_bonus"
        case "named item sets":
            return "named_item_sets"
        case "notes":
            return "notes"
        case "proficiency":
            return "proficiency_required"
        case "proficiency class":
            return "proficiency_required"
        case "race absolutely excluded":
            return "race_absolutely_excluded"
        case "race absolutely required":
            return "race_absolutely_required"
        case "required trait":
            return "required_trait"
        case "shield bonus":
            return "shield_bonus"
        case "shield type":
            return "shield_type"
        case "slot":
            return "item_slot"
        case "tips":
            return "tips"
        case "upgradeable?":
            return "upgradeable"
        case "use magical device dc":
            return "use_magic_device_dc"
        case "weapon type":
            return "weapon_type"
        case "weight":
            return "weight"
        case _:
            return original_name