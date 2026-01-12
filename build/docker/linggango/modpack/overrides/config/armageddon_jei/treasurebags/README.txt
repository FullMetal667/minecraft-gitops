================================================================================
Armageddon JEI - Treasure Bag Configuration
================================================================================

This directory contains JSON configuration files for treasure bag drops.
Each file defines what items drop from a specific treasure bag and their chances.

================================================================================
JSON Format
================================================================================

{
  "bag_item": "armageddon_mod:treasure_bag_name",
  "summon_item": "armageddon_mod:emerald_totem",
  "drops": [
    {
      "item": "minecraft:item_id",
      "chance": 1.0,
      "min_quantity": 1,
      "max_quantity": 1,
      "config_flag": "none"
    }
  ]
}

================================================================================
Field Descriptions
================================================================================

bag_item (required):
  - The resource location of the treasure bag item
  - Format: "modid:item_name"
  - Example: "armageddon_mod:arion_treasurebag"
  - If bag in-game doesn't have usage, check if you have the correct item ID here

summon_item (optional):
  - The resource location of the item used to summon the treasure bag
  - Format: "modid:item_name"
  - Example: "armageddon_mod:emerald_totem"

drops (required):
  - Array of drop entries

  Drop Entry Fields:

  item (required):
    - The resource location of the dropped item
    - Format: "modid:item_name"
    - Examples: "minecraft:diamond", "armageddon_mod:emerald_wrath"

  chance (required):
    - Probability of this item dropping (0.0 to 1.0)
    - 1.0 = 100% guaranteed drop
    - 0.5 = 50% chance
    - 0.01 = 1% chance

  min_quantity (optional, default: 1):
    - Minimum number of items dropped

  max_quantity (optional, default: 1):
    - Maximum number of items dropped
    - Example: min=3, max=5 means drops 3-5 items

  config_flag (optional, default: "none"):
    - Controls visibility in JEI based on Armageddon config settings
    - Checked when configs load - drops are filtered before JEI sees them
    - No tooltips or warnings - items simply won't appear if disabled
    - Options:
      - "none" - Always loaded and visible
      - "weapons_and_artifacts" - Only loaded if ARE_WEAPONS_AND_ARTIFACTS_DROP_FROM_TREASUREBAGS is enabled
      - "ores" - Only loaded if ARE_ORES_DROPPING_FROM_TREASUREBAGS is enabled
    - Check logs to see which drops were filtered based on config

================================================================================
Example
================================================================================

{
  "bag_item": "armageddon_mod:arion_treasurebag",
  "display_name": "Arion Treasure Bag",
  "drops": [
    {
      "item": "armageddon_mod:the_emerald_wrath",
      "chance": 0.30,
      "config_flag": "weapons_and_artifacts"
    },
    {
      "item": "minecraft:emerald",
      "chance": 1.0,
      "min_quantity": 3,
      "max_quantity": 4
    },
    {
      "item": "minecraft:ancient_debris",
      "chance": 0.09,
      "min_quantity": 5,
      "max_quantity": 5,
      "config_flag": "ores"
    }
  ]
}

This example shows:
- 30% chance to drop The Emerald Wrath (if weapons/artifacts enabled)
- 100% chance to drop 3-4 Emeralds
- 9% chance to drop 5 Ancient Debris (if ores enabled)

================================================================================
Reloading Configs
================================================================================

After editing these files, you can reload them without restarting Minecraft:

Option 1 - Standard Minecraft reload:
1. Save your changes to the JSON file
2. Run the command: /reload
3. Treasure bag configs will automatically reload with other server data

Option 2 - Dedicated command:
1. Save your changes to the JSON file
2. Run the command: /reloadtreasurebags (requires OP level 2)
3. Only reloads treasure bag configs (faster)

Either way, JEI will update to show your changes!

================================================================================
Adding New Treasure Bags
================================================================================

You can add custom treasure bag configurations:

1. Create a new JSON file in this directory (e.g., "my_custom_bag.json")
2. Use the format described above
3. Run /reloadtreasurebags to load it
4. The new bag will appear in JEI automatically

No need to modify the mod or restart Minecraft!

================================================================================
Troubleshooting
================================================================================

If a treasure bag doesn't appear in JEI:
1. Check the console/logs for errors
2. Verify JSON syntax (use a JSON validator)
3. Ensure the bag_item matches the actual item ID
4. Confirm all required fields are present

JSON Syntax Tips:
- Use double quotes for strings: "text"
- Numbers don't need quotes: 1.0, 5, 0.25
- Don't add comma after the last item in arrays or objects
- Use https://jsonlint.com/ to validate your JSON

================================================================================
