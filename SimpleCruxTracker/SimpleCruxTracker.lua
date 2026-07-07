-- Small Crux stack indicator for Arcanist. Adapted from ExoY's Crux Tracker,
-- stripped down to just the 3-pip display: no numeric/timer trackers, no audio
-- cues, no Spattering Disjunction proc tracking, and much smaller default
-- icons (26px vs. the original's 50-80px default).

local ADDON_NAME = "SimpleCruxTracker"
local SV_NAME = "SimpleCruxTrackerSV"

local EM = GetEventManager()
local WM = GetWindowManager()

local ARCANIST_CLASS_ID = 117
local CRUX_ABILITY_ID = 184220

-- Tweak these directly to change the look; there's no in-game settings menu.
local CONFIG = {
    iconSize = 26,
    spacing = 4,
    defaultPosX = 600,
    defaultPosY = 600,
}

local SV
local window
local icons = {}
local isUnlocked = false

local function HasArcanistSkillLine()
    for i = 1, 3 do
        local line = SKILLS_DATA_MANAGER:GetActiveClassSkillLine(i)
        if line and line:GetClassId() == ARCANIST_CLASS_ID then
            return true
        end
    end
    return false
end

local function ReadCurrentCrux()
    for i = 1, GetNumBuffs("player") do
        local _, _, _, _, stackCount, _, _, _, _, _, abilityId = GetUnitBuffInfo("player", i)
        if abilityId == CRUX_ABILITY_ID then
            return stackCount
        end
    end
    return 0
end

local function UpdateCruxDisplay(count)
    if not HasArcanistSkillLine() then
        window:SetHidden(true)
        return
    end
    for i = 1, 3 do
        if i <= count then
            icons[i].icon:SetColor(0, 1, 0, 1)
            icons[i].highlight:SetAlpha(0.8)
        else
            icons[i].icon:SetColor(1, 1, 1, 0.2)
            icons[i].highlight:SetAlpha(0)
        end
    end
    window:SetHidden(count == 0 and not isUnlocked)
end

local function BuildIcon(index)
    local name = ADDON_NAME .. "Icon" .. index
    local ctrl = WM:CreateControl(name, window, CT_CONTROL)
    ctrl:SetDimensions(CONFIG.iconSize, CONFIG.iconSize)
    ctrl:ClearAnchors()
    if index == 1 then
        ctrl:SetAnchor(LEFT, window, LEFT, 0, 0)
    else
        ctrl:SetAnchor(LEFT, icons[index - 1].ctrl, RIGHT, CONFIG.spacing, 0)
    end

    local back = WM:CreateControl(name .. "Back", ctrl, CT_TEXTURE)
    back:SetAnchorFill(ctrl)
    back:SetTexture("esoui/art/champion/champion_center_bg.dds")
    back:SetAlpha(0.8)

    local frame = WM:CreateControl(name .. "Frame", ctrl, CT_TEXTURE)
    frame:SetAnchorFill(ctrl)
    frame:SetTexture("esoui/art/champion/actionbar/champion_bar_slot_frame_disabled.dds")

    local icon = WM:CreateControl(name .. "Icon", ctrl, CT_TEXTURE)
    icon:ClearAnchors()
    icon:SetAnchor(CENTER, ctrl, CENTER, 0, 0)
    icon:SetDimensions(CONFIG.iconSize * 0.75, CONFIG.iconSize * 0.75)
    icon:SetTexture("/art/fx/texture/arcanist_trianglerune_01.dds")
    icon:SetColor(1, 1, 1, 0.2)

    local highlight = WM:CreateControl(name .. "Highlight", ctrl, CT_TEXTURE)
    highlight:SetAnchorFill(ctrl)
    highlight:SetTexture("esoui/art/champion/actionbar/champion_bar_world_selection.dds")
    highlight:SetColor(0, 1, 0, 0)

    return { ctrl = ctrl, icon = icon, highlight = highlight }
end

local function SetUnlocked(unlocked)
    isUnlocked = unlocked
    window:SetMouseEnabled(unlocked)
    window:SetMovable(unlocked)
    if unlocked then
        window:SetHidden(false)
    else
        UpdateCruxDisplay(ReadCurrentCrux())
    end
end

local function Initialize()
    SV = ZO_SavedVars:NewAccountWide(SV_NAME, 1, nil, {
        posX = CONFIG.defaultPosX,
        posY = CONFIG.defaultPosY,
    })

    window = WM:CreateTopLevelWindow(ADDON_NAME .. "Window")
    window:ClearAnchors()
    window:SetAnchor(TOPLEFT, GuiRoot, TOPLEFT, SV.posX, SV.posY)
    window:SetDimensions(3 * CONFIG.iconSize + 2 * CONFIG.spacing, CONFIG.iconSize)
    window:SetMouseEnabled(false)
    window:SetMovable(false)
    window:SetClampedToScreen(true)
    window:SetHidden(true)
    window:SetHandler("OnMoveStop", function()
        SV.posX = window:GetLeft()
        SV.posY = window:GetTop()
    end)

    for i = 1, 3 do
        icons[i] = BuildIcon(i)
    end

    EM:RegisterForEvent(ADDON_NAME, EVENT_EFFECT_CHANGED, function(_, changeType, _, _, unitTag, _, _, stackCount)
        if changeType == EFFECT_RESULT_FADED then
            UpdateCruxDisplay(0)
        else
            UpdateCruxDisplay(stackCount)
        end
    end)
    EM:AddFilterForEvent(ADDON_NAME, EVENT_EFFECT_CHANGED, REGISTER_FILTER_ABILITY_ID, CRUX_ABILITY_ID)
    EM:AddFilterForEvent(ADDON_NAME, EVENT_EFFECT_CHANGED, REGISTER_FILTER_UNIT_TAG, "player")

    EM:RegisterForEvent(ADDON_NAME .. "Activated", EVENT_PLAYER_ACTIVATED, function()
        UpdateCruxDisplay(ReadCurrentCrux())
    end)
    EM:RegisterForEvent(ADDON_NAME .. "SkillsUpdated", EVENT_SKILLS_FULL_UPDATE, function()
        UpdateCruxDisplay(ReadCurrentCrux())
    end)

    SLASH_COMMANDS["/crux"] = function(arg)
        if arg == "unlock" then
            SetUnlocked(true)
            d("SimpleCruxTracker: unlocked, drag to reposition. Type /crux lock when done.")
        elseif arg == "lock" then
            SetUnlocked(false)
            d("SimpleCruxTracker: locked.")
        else
            d("SimpleCruxTracker: /crux unlock | /crux lock")
        end
    end

    UpdateCruxDisplay(ReadCurrentCrux())
end

local function OnAddonLoaded(_, name)
    if name ~= ADDON_NAME then return end
    EM:UnregisterForEvent(ADDON_NAME, EVENT_ADD_ON_LOADED)
    Initialize()
end
EM:RegisterForEvent(ADDON_NAME, EVENT_ADD_ON_LOADED, OnAddonLoaded)
