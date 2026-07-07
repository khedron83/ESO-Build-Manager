WornGearSV = WornGearSV or {}

local EQUIP_SLOTS = {
    { id = EQUIP_SLOT_HEAD,        name = "Head" },
    { id = EQUIP_SLOT_NECK,        name = "Neck" },
    { id = EQUIP_SLOT_CHEST,       name = "Chest" },
    { id = EQUIP_SLOT_SHOULDERS,   name = "Shoulders" },
    { id = EQUIP_SLOT_HAND,        name = "Hands" },
    { id = EQUIP_SLOT_WAIST,       name = "Waist" },
    { id = EQUIP_SLOT_LEGS,        name = "Legs" },
    { id = EQUIP_SLOT_FEET,        name = "Feet" },
    { id = EQUIP_SLOT_RING1,       name = "Ring 1" },
    { id = EQUIP_SLOT_RING2,       name = "Ring 2" },
    { id = EQUIP_SLOT_MAIN_HAND,   name = "Main Hand" },
    { id = EQUIP_SLOT_OFF_HAND,    name = "Off Hand" },
    { id = EQUIP_SLOT_BACKUP_MAIN, name = "Backup Main" },
    { id = EQUIP_SLOT_BACKUP_OFF,  name = "Backup Off" },
}

local ARMOR_TYPE_NAME = {
    [ARMORTYPE_LIGHT]  = "Light",
    [ARMORTYPE_MEDIUM] = "Medium",
    [ARMORTYPE_HEAVY]  = "Heavy",
}

local WEAPON_TYPE_NAME = {
    [WEAPONTYPE_SWORD]             = "Sword",
    [WEAPONTYPE_AXE]               = "Axe",
    [WEAPONTYPE_HAMMER]            = "Mace",
    [WEAPONTYPE_DAGGER]            = "Dagger",
    [WEAPONTYPE_TWO_HANDED_SWORD]  = "Greatsword",
    [WEAPONTYPE_TWO_HANDED_AXE]    = "Battle Axe",
    [WEAPONTYPE_TWO_HANDED_HAMMER] = "Maul",
    [WEAPONTYPE_BOW]               = "Bow",
    [WEAPONTYPE_FIRE_STAFF]        = "Inferno Staff",
    [WEAPONTYPE_FROST_STAFF]       = "Ice Staff",
    [WEAPONTYPE_LIGHTNING_STAFF]   = "Lightning Staff",
    [WEAPONTYPE_HEALING_STAFF]     = "Restoration Staff",
    [WEAPONTYPE_SHIELD]            = "Shield",
}

local QUALITY_NAME = {
    [ITEM_DISPLAY_QUALITY_TRASH]          = "Trash",
    [ITEM_DISPLAY_QUALITY_NORMAL]         = "Normal",
    [ITEM_DISPLAY_QUALITY_ARCANE]         = "Fine",
    [ITEM_DISPLAY_QUALITY_MAGIC]          = "Superior",
    [ITEM_DISPLAY_QUALITY_ARTIFACT]       = "Epic",
    [ITEM_DISPLAY_QUALITY_LEGENDARY]      = "Legendary",
    [ITEM_DISPLAY_QUALITY_MYTHIC_OVERRIDE] = "Mythic",
}

local TRAIT_NAME = {
    -- Armor
    [ITEM_TRAIT_TYPE_ARMOR_DIVINES]        = "Divines",
    [ITEM_TRAIT_TYPE_ARMOR_INFUSED]        = "Infused",
    [ITEM_TRAIT_TYPE_ARMOR_IMPENETRABLE]   = "Impenetrable",
    [ITEM_TRAIT_TYPE_ARMOR_REINFORCED]     = "Reinforced",
    [ITEM_TRAIT_TYPE_ARMOR_STURDY]         = "Sturdy",
    [ITEM_TRAIT_TYPE_ARMOR_TRAINING]       = "Training",
    [ITEM_TRAIT_TYPE_ARMOR_WELL_FITTED]    = "Well-Fitted",
    [ITEM_TRAIT_TYPE_ARMOR_NIRNHONED]      = "Nirnhoned",
    [ITEM_TRAIT_TYPE_ARMOR_INTRICATE]      = "Intricate",
    [ITEM_TRAIT_TYPE_ARMOR_ORNATE]         = "Ornate",
    -- Weapon
    [ITEM_TRAIT_TYPE_WEAPON_SHARPENED]     = "Sharpened",
    [ITEM_TRAIT_TYPE_WEAPON_PRECISE]       = "Precise",
    [ITEM_TRAIT_TYPE_WEAPON_NIRNHONED]     = "Nirnhoned",
    [ITEM_TRAIT_TYPE_WEAPON_DEFENDING]     = "Defending",
    [ITEM_TRAIT_TYPE_WEAPON_POWERED]       = "Powered",
    [ITEM_TRAIT_TYPE_WEAPON_CHARGED]       = "Charged",
    [ITEM_TRAIT_TYPE_WEAPON_DECISIVE]      = "Decisive",
    [ITEM_TRAIT_TYPE_WEAPON_INFUSED]       = "Infused",
    [ITEM_TRAIT_TYPE_WEAPON_TRAINING]      = "Training",
    [ITEM_TRAIT_TYPE_WEAPON_INTRICATE]     = "Intricate",
    [ITEM_TRAIT_TYPE_WEAPON_ORNATE]        = "Ornate",
    -- Jewelry
    [ITEM_TRAIT_TYPE_JEWELRY_ARCANE]       = "Arcane",
    [ITEM_TRAIT_TYPE_JEWELRY_HEALTHY]      = "Healthy",
    [ITEM_TRAIT_TYPE_JEWELRY_ROBUST]       = "Robust",
    [ITEM_TRAIT_TYPE_JEWELRY_SWIFT]        = "Swift",
    [ITEM_TRAIT_TYPE_JEWELRY_TRIUNE]       = "Triune",
    [ITEM_TRAIT_TYPE_JEWELRY_INFUSED]      = "Infused",
    [ITEM_TRAIT_TYPE_JEWELRY_PROTECTIVE]   = "Protective",
    [ITEM_TRAIT_TYPE_JEWELRY_HARMONY]      = "Harmony",
    [ITEM_TRAIT_TYPE_JEWELRY_BLOODTHIRSTY] = "Bloodthirsty",
    [ITEM_TRAIT_TYPE_JEWELRY_INTRICATE]    = "Intricate",
    [ITEM_TRAIT_TYPE_JEWELRY_ORNATE]       = "Ornate",
}

local HOTBARS = {
    { id = HOTBAR_CATEGORY_PRIMARY, name = "Front Bar" },
    { id = HOTBAR_CATEGORY_BACKUP,  name = "Back Bar" },
}

-- All skill types to capture (except CHAMPION which is handled separately)
local SKILL_TYPES = {
    { type = SKILL_TYPE_CLASS,     key = "class" },
    { type = SKILL_TYPE_WEAPON,    key = "weapon" },
    { type = SKILL_TYPE_ARMOR,     key = "armor" },
    { type = SKILL_TYPE_GUILD,     key = "guild" },
    { type = SKILL_TYPE_AVA,       key = "ava" },
    { type = SKILL_TYPE_WORLD,     key = "world" },
    { type = SKILL_TYPE_RACIAL,    key = "racial" },
    { type = SKILL_TYPE_TRADESKILL,key = "craft" },
}

-- ── Armory capture ────────────────────────────────────────────────────────────

local function ExtractGear(buildIndex)
    local gear = {}
    for _, slot in ipairs(EQUIP_SLOTS) do
        local state, bagId, slotIndex = GetArmoryBuildEquipSlotInfo(buildIndex, slot.id)
        if state == ARMORY_BUILD_EQUIP_SLOT_STATE_VALID then
            local link = GetItemLink(bagId, slotIndex)
            if link ~= "" then
                local hasSet, setName = GetItemLinkSetInfo(link)
                local quality = GetItemLinkDisplayQuality(link)
                local hasCharges, enchantHeader = GetItemLinkEnchantInfo(link)
                gear[slot.name] = {
                    name    = GetItemLinkName(link),
                    setName = hasSet and setName or "",
                    quality = QUALITY_NAME[quality] or "Normal",
                    link    = link,
                    enchant = hasCharges and enchantHeader:gsub(" Enchantment$", "") or "",
                    weight  = WEAPON_TYPE_NAME[GetItemLinkWeaponType(link)]
                              or ARMOR_TYPE_NAME[GetItemLinkArmorType(link)] or "",
                    trait   = TRAIT_NAME[GetItemLinkTraitType(link)] or "",
                }
            end
        end
    end
    return gear
end

local function ReadLiveSkills()
    local skills = {}
    for _, bar in ipairs(HOTBARS) do
        local barSkills = {}
        for slotIndex = 3, 8 do
            local displayName = GetSlotName(slotIndex, bar.id) or ""
            local baseName = displayName
            if displayName ~= "" then
                local boundId = GetSlotBoundId(slotIndex, bar.id)
                if boundId and boundId ~= 0 then
                    -- boundId IS the craftedAbilityId directly for scribed slots (there are
                    -- only ~12 grimoires, so these are small IDs like 12, vs the 5-digit
                    -- regular ability IDs everything else has). GetCraftedAbilityDisplayName
                    -- returns "" for non-scribed slots, so this doubles as the scribed check.
                    local craftedName = GetCraftedAbilityDisplayName(boundId)
                    if craftedName and craftedName ~= "" then baseName = craftedName end
                end
            end
            barSkills[#barSkills + 1] = { name = displayName, base = baseName }
        end
        skills[bar.name] = barSkills
    end
    return skills
end

local function FindActiveBuildName(builds)
    local wornLinks = {}
    for _, slot in ipairs(EQUIP_SLOTS) do
        wornLinks[slot.name] = GetItemLink(BAG_WORN, slot.id)
    end
    local bestMatch, bestCount = nil, 0
    for buildName, buildData in pairs(builds) do
        if type(buildData) == "table" and buildName:sub(1,2) ~= "__" then
            local gear = buildData.gear or {}
            local matchCount = 0
            for slotName, link in pairs(wornLinks) do
                if link ~= "" and gear[slotName] and gear[slotName].link == link then
                    matchCount = matchCount + 1
                end
            end
            if matchCount > bestCount then
                bestCount = matchCount
                bestMatch = buildName
            end
        end
    end
    return bestCount >= 2 and bestMatch or nil
end

local function ExtractAttributes(buildIndex)
    return {
        health  = GetArmoryBuildAttributeSpentPoints(buildIndex, ATTRIBUTE_HEALTH),
        magicka = GetArmoryBuildAttributeSpentPoints(buildIndex, ATTRIBUTE_MAGICKA),
        stamina = GetArmoryBuildAttributeSpentPoints(buildIndex, ATTRIBUTE_STAMINA),
    }
end

local function ExtractChampionPoints(buildIndex)
    local cp = {}
    for i = 1, GetNumChampionDisciplines() do
        local disciplineId = GetChampionDisciplineId(i)
        local points = GetArmoryBuildChampionSpentPointsByDiscipline(buildIndex, disciplineId)
        if points and points > 0 then
            cp[GetChampionDisciplineName(disciplineId)] = points
        end
    end
    return cp
end

local function ReadLiveChampionPoints()
    local cp = {}
    local start, finish = GetAssignableChampionBarStartAndEndSlots()
    for slotIndex = start, finish do
        local skillId = GetSlotBoundId(slotIndex, HOTBAR_CATEGORY_CHAMPION)
        if skillId and skillId ~= 0 then
            local disciplineId = GetRequiredChampionDisciplineIdForSlot(slotIndex, HOTBAR_CATEGORY_CHAMPION)
            local disciplineName = GetChampionDisciplineName(disciplineId)
            local skillName = GetChampionSkillName(skillId)
            local pts = GetNumPointsSpentOnChampionSkill(skillId)
            if skillName and pts and pts > 0 then
                if not cp[disciplineName] then cp[disciplineName] = {} end
                cp[disciplineName][skillName] = pts
            end
        end
    end
    return cp
end

-- ── Character data capture ────────────────────────────────────────────────────

local function ReadSkillLines()
    local result = {}
    local playerClassId = GetUnitClassId("player")
    for _, st in ipairs(SKILL_TYPES) do
        local lines = {}
        for i = 1, GetNumSkillLines(st.type) do
            local lineId = GetSkillLineId(st.type, i)
            local name = GetSkillLineNameById(lineId)
            local rank, _, _, isDiscovered, _, _, isClassMastery = GetSkillLineDynamicInfo(st.type, i)
            if name and name ~= "" and isDiscovered and not isClassMastery then
                local entry = { name = name, rank = rank or 0 }
                if st.type == SKILL_TYPE_CLASS then
                    local lineClassId = GetSkillLineClassId(st.type, i)
                    entry.native = (lineClassId == playerClassId)
                end
                lines[#lines + 1] = entry
            end
        end
        result[st.key] = lines
    end
    return result
end

local function ReadChampionData()
    local disciplines = {}
    local totalSpent = 0
    local totalEarned = GetPlayerChampionPointsEarned()
    for i = 1, GetNumChampionDisciplines() do
        local disciplineId = GetChampionDisciplineId(i)
        local name = GetChampionDisciplineName(disciplineId)
        local stars = {}
        local spent = 0
        for j = 1, GetNumChampionDisciplineSkills(i) do
            local skillId = GetChampionSkillId(i, j)
            local pts = GetNumPointsSpentOnChampionSkill(skillId)
            if pts and pts > 0 then
                local skillName = GetChampionSkillName(skillId)
                stars[skillName] = pts
                spent = spent + pts
            end
        end
        disciplines[name] = { spent = spent, stars = stars }
        totalSpent = totalSpent + spent
    end
    return {
        earned  = totalEarned,
        spent   = totalSpent,
        unspent = totalEarned - totalSpent,
        disciplines = disciplines,
    }
end

local function ReadInventory()
    -- Personal inventory only: the bank is one shared pool for all characters
    -- (see bankCurrencies below), so it must never be folded into a character's
    -- own item/soul gem counts here.
    local items = {}
    local soulsEmpty = 0
    local soulsFilled = 0
    local bagId = BAG_BACKPACK
    for i = 0, GetBagSize(bagId) - 1 do
        local name = GetItemName(bagId, i)
        -- Stolen items sit in their own stack apart from an identically-named
        -- legit stack (e.g. 200 owned lockpicks + 5 stolen ones as two separate
        -- slots) and aren't usable for most purposes until fenced, so they're
        -- excluded entirely rather than counted alongside the real total.
        if name and name ~= "" and not IsItemStolen(bagId, i) then
            local _, count = GetItemInfo(bagId, i)
            items[#items + 1] = { name = name, count = count or 1, bag = "Backpack" }
            if IsItemSoulGem(SOUL_GEM_TYPE_FILLED, bagId, i) then
                soulsFilled = soulsFilled + (count or 1)
            elseif IsItemSoulGem(SOUL_GEM_TYPE_EMPTY, bagId, i) then
                soulsEmpty = soulsEmpty + (count or 1)
            end
        end
    end
    return items, soulsEmpty, soulsFilled
end

-- Writ turn-ins don't have a clean "already claimed today" API the way the
-- daily random dungeon does (see dailies.dungeonDone below), so this tracks
-- the last time this character's Writ Voucher currency went up (all 7 writ
-- types pay vouchers) and compares that against today's reset boundary.
-- Persisted per-character since Snapshot() overwrites WornGearSV[charName]
-- wholesale on every call.
local function ReadDailyWritStatus(charName)
    local tracking = WornGearSV[charName] and WornGearSV[charName].dailyTracking
    local lastGain = tracking and tracking.lastWritVoucherGain or 0
    local startOfToday = GetTimeStamp() - GetSecondsSinceMidnight()
    return lastGain >= startOfToday
end

local function ReadCharData()
    local alliance = GetUnitAlliance("player")
    local items, soulsEmpty, soulsFilled = ReadInventory()
    local invBonus, _, stamBonus, _, speedBonus = GetRidingStats()
    local charName = GetUnitName("player")

    return {
        bio = {
            name           = GetUnitName("player"),
            class          = GetUnitClass("player"),
            race           = GetUnitRace("player"),
            alliance       = GetAllianceName(alliance),
            avARank        = GetUnitAvARank("player"),
            level          = GetUnitLevel("player"),
            championPoints = GetUnitChampionPoints("player"),
            isChampion     = CanUnitGainChampionPoints("player"),
            secondsPlayed  = GetSecondsPlayed(),
            skillPoints    = GetAvailableSkillPoints(),
            lastUpdated    = GetTimeStamp(),
        },
        stats = {
            healthMax      = GetPlayerStat(STAT_HEALTH_MAX,          STAT_BONUS_OPTION_APPLY_BONUS),
            staminaMax     = GetPlayerStat(STAT_STAMINA_MAX,         STAT_BONUS_OPTION_APPLY_BONUS),
            magickaMax     = GetPlayerStat(STAT_MAGICKA_MAX,         STAT_BONUS_OPTION_APPLY_BONUS),
            healthRegen    = GetPlayerStat(STAT_HEALTH_REGEN_COMBAT, STAT_BONUS_OPTION_APPLY_BONUS),
            staminaRegen   = GetPlayerStat(STAT_STAMINA_REGEN_COMBAT,STAT_BONUS_OPTION_APPLY_BONUS),
            magickaRegen   = GetPlayerStat(STAT_MAGICKA_REGEN_COMBAT,STAT_BONUS_OPTION_APPLY_BONUS),
            spellDamage    = GetPlayerStat(STAT_SPELL_POWER,         STAT_BONUS_OPTION_APPLY_BONUS),
            weaponDamage   = GetPlayerStat(STAT_ATTACK_POWER,        STAT_BONUS_OPTION_APPLY_BONUS),
            critChance     = GetPlayerStat(STAT_SPELL_CRITICAL,      STAT_BONUS_OPTION_APPLY_BONUS),
            physResist     = GetPlayerStat(STAT_PHYSICAL_RESIST,     STAT_BONUS_OPTION_APPLY_BONUS),
            spellResist    = GetPlayerStat(STAT_SPELL_RESIST,        STAT_BONUS_OPTION_APPLY_BONUS),
            critResist     = GetPlayerStat(STAT_CRITICAL_RESISTANCE, STAT_BONUS_OPTION_APPLY_BONUS),
        },
        mount = {
            speed    = speedBonus,
            stamina  = stamBonus,
            capacity = invBonus,
        },
        -- On-person only (carried by this character). Gold uses ESO's dedicated
        -- money function; the rest go through GetCarriedCurrencyAmount.
        currencies = {
            gold          = GetCurrentMoney(),
            ap            = GetCarriedCurrencyAmount(CURT_ALLIANCE_POINTS),
            telvar        = GetCarriedCurrencyAmount(CURT_TELVAR_STONES),
            writVouchers  = GetCarriedCurrencyAmount(CURT_WRIT_VOUCHERS),
            undauntedKeys = GetCarriedCurrencyAmount(CURT_UNDAUNTED_KEYS),
        },
        -- Shared account-wide totals: the bank (one pool for all characters) plus
        -- currencies that only ever live at the account level (Crowns etc).
        bankCurrencies = {
            gold          = GetBankedMoney(),
            ap            = GetCurrencyAmount(CURT_ALLIANCE_POINTS, CURRENCY_LOCATION_BANK),
            telvar        = GetCurrencyAmount(CURT_TELVAR_STONES,   CURRENCY_LOCATION_BANK),
            writVouchers  = GetCurrencyAmount(CURT_WRIT_VOUCHERS,   CURRENCY_LOCATION_BANK),
            undauntedKeys = GetCurrencyAmount(CURT_UNDAUNTED_KEYS,  CURRENCY_LOCATION_BANK),
            crowns        = GetCurrencyAmount(CURT_CROWNS,         CURRENCY_LOCATION_ACCOUNT),
            crownGems     = GetCurrencyAmount(CURT_CROWN_GEMS,     CURRENCY_LOCATION_ACCOUNT),
            endeavorSeals = GetCurrencyAmount(CURT_ENDEAVOR_SEALS, CURRENCY_LOCATION_ACCOUNT),
        },
        bag = {
            used       = GetNumBagUsedSlots(BAG_BACKPACK),
            size       = GetBagSize(BAG_BACKPACK),
            bankUsed   = GetNumBagUsedSlots(BAG_BANK),
            bankSize   = GetBagSize(BAG_BANK),
            soulsEmpty  = soulsEmpty,
            soulsFilled = soulsFilled,
        },
        skills    = ReadSkillLines(),
        champion  = ReadChampionData(),
        inventory = items,
        -- IsActivityEligibleForDailyReward is server-authoritative, so unlike
        -- the writ check it's correct no matter when in the session this runs
        -- (even if the dungeon was completed in an earlier session today).
        dailies = {
            dungeonDone = not IsActivityEligibleForDailyReward(LFG_ACTIVITY_DUNGEON),
            writsDone   = ReadDailyWritStatus(charName),
        },
    }
end

-- ── Snapshot ──────────────────────────────────────────────────────────────────

local function Snapshot()
    local charName = GetUnitName("player")
    -- dailyTracking lives outside the builds table but Snapshot() below
    -- replaces WornGearSV[charName] wholesale, so it has to be carried over
    -- explicitly rather than just left alone.
    local prevDailyTracking = WornGearSV[charName] and WornGearSV[charName].dailyTracking
    local builds = {}
    local count = 0

    for i = 1, MAX_NUM_ARMORY_BUILDS do
        local buildName = GetArmoryBuildName(i)
        if buildName and buildName ~= "" then
            count = count + 1
            local prevData       = WornGearSV[charName] and WornGearSV[charName][buildName]
            local prevSkills     = prevData and prevData.skills     or nil
            local prevCp         = prevData and prevData.cp         or nil
            local prevSubclasses = prevData and prevData.subclasses or nil
            local prevMasteries  = prevData and prevData.masteries  or nil
            local keepCp = false
            if prevCp then
                for _, v in pairs(prevCp) do
                    if type(v) == "table" then keepCp = true; break end
                end
            end
            builds[buildName] = {
                gear       = ExtractGear(i),
                skills     = prevSkills or {},
                subclasses = prevSubclasses or {},
                masteries  = prevMasteries  or {},
                attributes = ExtractAttributes(i),
                cp         = keepCp and prevCp or ExtractChampionPoints(i),
            }
        end
    end

    local activeBuild = FindActiveBuildName(builds)
    if activeBuild then
        builds[activeBuild].skills = ReadLiveSkills()
        local liveCp = ReadLiveChampionPoints()
        if next(liveCp) then
            builds[activeBuild].cp = liveCp
        end
        d("WornGear: captured skills + CP stars for " .. activeBuild)
    end

    if activeBuild then
        local playerClassId = GetUnitClassId("player")
        local subclasses = {}
        for i = 1, GetNumSkillLines(SKILL_TYPE_CLASS) do
            local lineClassId = GetSkillLineClassId(SKILL_TYPE_CLASS, i)
            if lineClassId ~= playerClassId then
                local _, _, isActive, _, _, _, isClassMastery = GetSkillLineDynamicInfo(SKILL_TYPE_CLASS, i)
                if isActive and not isClassMastery then
                    local lineId = GetSkillLineId(SKILL_TYPE_CLASS, i)
                    local name = GetSkillLineNameById(lineId)
                    if name and name ~= "" then
                        subclasses[#subclasses + 1] = name
                    end
                end
            end
        end
        builds[activeBuild].subclasses = subclasses

        local masteries = {}
        for i = 1, GetNumSkillLines(SKILL_TYPE_CLASS) do
            local _, _, _, isDiscovered, _, _, isClassMastery = GetSkillLineDynamicInfo(SKILL_TYPE_CLASS, i)
            if isClassMastery and isDiscovered then
                for j = 1, GetNumSkillAbilities(SKILL_TYPE_CLASS, i) do
                    local name, _, _, _, _, purchased = GetSkillAbilityInfo(SKILL_TYPE_CLASS, i, j)
                    if purchased and name and name ~= "" then
                        masteries[#masteries + 1] = name
                    end
                end
            end
        end
        builds[activeBuild].masteries = masteries
    end

    -- Capture full character data (bio, stats, skills, inventory, etc.)
    builds["__char__"] = ReadCharData()

    WornGearSV[charName] = builds
    WornGearSV[charName].dailyTracking = prevDailyTracking or { lastWritVoucherGain = 0 }
    d("WornGear: saved " .. count .. " armory builds for " .. charName)
end

-- EVENT_PLAYER_ACTIVATED fires after every loading screen (zone changes, dungeon
-- room transitions, deaths, wayshrines), not just true login. Only snapshot the
-- first time per session; EVENT_ARMORY_BUILD_RESTORE_RESPONSE handles updates
-- when a build is actually swapped mid-session.
local hasSnapshotted = false
EVENT_MANAGER:RegisterForEvent("WornGear", EVENT_PLAYER_ACTIVATED, function()
    if hasSnapshotted then return end
    hasSnapshotted = true
    zo_callLater(Snapshot, 3000)
end)

EVENT_MANAGER:RegisterForEvent("WornGear_Restore", EVENT_ARMORY_BUILD_RESTORE_RESPONSE, function(_, result, _)
    if result == ARMORY_BUILD_RESTORE_RESULT_SUCCESS then
        zo_callLater(Snapshot, 1500)
    end
end)

-- Recorded live (not just at Snapshot time) so it's captured even if the
-- character logs out shortly after turning in a writ, before another
-- snapshot would otherwise happen. Also patches __char__.dailies.writsDone
-- directly, same reasoning as RefreshDungeonDaily below — that's the field
-- the app actually reads, and it otherwise wouldn't update until the next
-- full Snapshot().
EVENT_MANAGER:RegisterForEvent("WornGear_WritVoucher", EVENT_WRIT_VOUCHER_UPDATE, function(_, newAmount, oldAmount)
    if newAmount <= oldAmount then return end
    local charName = GetUnitName("player")
    WornGearSV[charName] = WornGearSV[charName] or {}
    WornGearSV[charName].dailyTracking = WornGearSV[charName].dailyTracking or {}
    WornGearSV[charName].dailyTracking.lastWritVoucherGain = GetTimeStamp()

    local char = WornGearSV[charName].__char__
    if char then
        char.dailies = char.dailies or {}
        char.dailies.writsDone = true
    end
end)

-- Snapshot() only runs once per session (see hasSnapshotted above), so without
-- this the dungeon flag would stay stale at whatever it was when you logged
-- in until your next session, even though IsActivityEligibleForDailyReward
-- itself would report correctly if re-queried right now. Patch just that one
-- field in place rather than re-running the full Snapshot().
local function RefreshDungeonDaily()
    local charName = GetUnitName("player")
    local char = WornGearSV[charName] and WornGearSV[charName].__char__
    if not char then return end
    char.dailies = char.dailies or {}
    char.dailies.dungeonDone = not IsActivityEligibleForDailyReward(LFG_ACTIVITY_DUNGEON)
end
EVENT_MANAGER:RegisterForEvent("WornGear_DungeonComplete", EVENT_ACTIVITY_FINDER_ACTIVITY_COMPLETE, RefreshDungeonDaily)
EVENT_MANAGER:RegisterForEvent("WornGear_DungeonCooldown", EVENT_ACTIVITY_FINDER_COOLDOWNS_UPDATE, RefreshDungeonDaily)
