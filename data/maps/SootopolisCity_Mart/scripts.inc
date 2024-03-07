# 1 "data/maps/SootopolisCity_Mart/scripts.pory"

# 2 "data/maps/SootopolisCity_Mart/scripts.pory"
SootopolisCity_Mart_MapScripts::
# 3 "data/maps/SootopolisCity_Mart/scripts.pory"
	.byte 0
# 4 "data/maps/SootopolisCity_Mart/scripts.pory"

# 5 "data/maps/SootopolisCity_Mart/scripts.pory"
SootopolisCity_Mart_EventScript_Clerk::
# 6 "data/maps/SootopolisCity_Mart/scripts.pory"
	lock
# 7 "data/maps/SootopolisCity_Mart/scripts.pory"
	faceplayer
# 8 "data/maps/SootopolisCity_Mart/scripts.pory"
	message gText_HowMayIServeYou
# 9 "data/maps/SootopolisCity_Mart/scripts.pory"
	waitmessage
# 10 "data/maps/SootopolisCity_Mart/scripts.pory"
	pokemart SootopolisCity_Mart_Pokemart
# 11 "data/maps/SootopolisCity_Mart/scripts.pory"
	msgbox gText_PleaseComeAgain, MSGBOX_DEFAULT
# 12 "data/maps/SootopolisCity_Mart/scripts.pory"
	release
# 13 "data/maps/SootopolisCity_Mart/scripts.pory"
	end
# 14 "data/maps/SootopolisCity_Mart/scripts.pory"

# 15 "data/maps/SootopolisCity_Mart/scripts.pory"
	.align 2
# 16 "data/maps/SootopolisCity_Mart/scripts.pory"
SootopolisCity_Mart_Pokemart:
# 17 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_ULTRA_BALL
# 18 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_QUICK_BALL
# 19 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_NET_BALL
# 20 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_RARE_CANDY
# 21 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_MAX_REPEL
# 22 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_ABILITY_CAPSULE
# 23 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_ABILITY_PATCH
# 24 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_FLAME_PLATE
# 25 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_SPLASH_PLATE
# 26 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_ZAP_PLATE
# 27 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_MEADOW_PLATE
# 28 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_ICICLE_PLATE
# 29 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_FIST_PLATE
# 30 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_TOXIC_PLATE
# 31 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_EARTH_PLATE
# 32 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_SKY_PLATE
# 33 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_MIND_PLATE
# 34 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_INSECT_PLATE
# 35 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_STONE_PLATE
# 36 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_SPOOKY_PLATE
# 37 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_DRACO_PLATE
# 38 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_DREAD_PLATE
# 39 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_IRON_PLATE
# 40 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_PIXIE_PLATE
# 41 "data/maps/SootopolisCity_Mart/scripts.pory"
	.2byte ITEM_NONE
# 42 "data/maps/SootopolisCity_Mart/scripts.pory"
	release
# 43 "data/maps/SootopolisCity_Mart/scripts.pory"
	end
# 44 "data/maps/SootopolisCity_Mart/scripts.pory"

# 45 "data/maps/SootopolisCity_Mart/scripts.pory"
SootopolisCity_Mart_EventScript_FatMan::
# 46 "data/maps/SootopolisCity_Mart/scripts.pory"
	lock
# 47 "data/maps/SootopolisCity_Mart/scripts.pory"
	faceplayer
# 48 "data/maps/SootopolisCity_Mart/scripts.pory"
	goto_if_ge VAR_SKY_PILLAR_STATE, 2, SootopolisCity_Mart_EventScript_FatManNoLegendaries
# 49 "data/maps/SootopolisCity_Mart/scripts.pory"
	goto_if_unset FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN, SootopolisCity_Mart_EventScript_FatManNoLegendaries
# 50 "data/maps/SootopolisCity_Mart/scripts.pory"
	msgbox SootopolisCity_Mart_Text_TooScaryOutside, MSGBOX_DEFAULT
# 51 "data/maps/SootopolisCity_Mart/scripts.pory"
	release
# 52 "data/maps/SootopolisCity_Mart/scripts.pory"
	end
# 53 "data/maps/SootopolisCity_Mart/scripts.pory"

# 54 "data/maps/SootopolisCity_Mart/scripts.pory"
SootopolisCity_Mart_EventScript_FatManNoLegendaries::
# 55 "data/maps/SootopolisCity_Mart/scripts.pory"
	msgbox SootopolisCity_Mart_Text_PPUpIsGreat, MSGBOX_DEFAULT
# 56 "data/maps/SootopolisCity_Mart/scripts.pory"
	release
# 57 "data/maps/SootopolisCity_Mart/scripts.pory"
	end
# 58 "data/maps/SootopolisCity_Mart/scripts.pory"

# 59 "data/maps/SootopolisCity_Mart/scripts.pory"
SootopolisCity_Mart_EventScript_Gentleman::
# 60 "data/maps/SootopolisCity_Mart/scripts.pory"
	lock
# 61 "data/maps/SootopolisCity_Mart/scripts.pory"
	faceplayer
# 62 "data/maps/SootopolisCity_Mart/scripts.pory"
	goto_if_ge VAR_SKY_PILLAR_STATE, 2, SootopolisCity_Mart_EventScript_GentlemanNoLegendaries
# 63 "data/maps/SootopolisCity_Mart/scripts.pory"
	goto_if_unset FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN, SootopolisCity_Mart_EventScript_GentlemanNoLegendaries
# 64 "data/maps/SootopolisCity_Mart/scripts.pory"
	msgbox SootopolisCity_Mart_Text_DidSomethingAwaken, MSGBOX_DEFAULT
# 65 "data/maps/SootopolisCity_Mart/scripts.pory"
	release
# 66 "data/maps/SootopolisCity_Mart/scripts.pory"
	end
# 67 "data/maps/SootopolisCity_Mart/scripts.pory"

# 68 "data/maps/SootopolisCity_Mart/scripts.pory"
SootopolisCity_Mart_EventScript_GentlemanNoLegendaries::
# 69 "data/maps/SootopolisCity_Mart/scripts.pory"
	msgbox SootopolisCity_Mart_Text_FullRestoreItemOfDreams, MSGBOX_DEFAULT
# 70 "data/maps/SootopolisCity_Mart/scripts.pory"
	release
# 71 "data/maps/SootopolisCity_Mart/scripts.pory"
	end
# 72 "data/maps/SootopolisCity_Mart/scripts.pory"

# 73 "data/maps/SootopolisCity_Mart/scripts.pory"
SootopolisCity_Mart_Text_PPUpIsGreat:
# 74 "data/maps/SootopolisCity_Mart/scripts.pory"
	.string "PP UP is great!\p"
# 75 "data/maps/SootopolisCity_Mart/scripts.pory"
	.string "It raises the POWER POINTS, the PP,\n"
# 76 "data/maps/SootopolisCity_Mart/scripts.pory"
	.string "of a POKéMON move.$"
# 77 "data/maps/SootopolisCity_Mart/scripts.pory"

# 78 "data/maps/SootopolisCity_Mart/scripts.pory"
SootopolisCity_Mart_Text_TooScaryOutside:
# 79 "data/maps/SootopolisCity_Mart/scripts.pory"
	.string "What…\n"
# 80 "data/maps/SootopolisCity_Mart/scripts.pory"
	.string "What is happening?\p"
# 81 "data/maps/SootopolisCity_Mart/scripts.pory"
	.string "I really want to know, but it's too\n"
# 82 "data/maps/SootopolisCity_Mart/scripts.pory"
	.string "scary to go outside.$"
# 83 "data/maps/SootopolisCity_Mart/scripts.pory"

# 84 "data/maps/SootopolisCity_Mart/scripts.pory"
SootopolisCity_Mart_Text_FullRestoreItemOfDreams:
# 85 "data/maps/SootopolisCity_Mart/scripts.pory"
	.string "Do you know FULL RESTORE?\p"
# 86 "data/maps/SootopolisCity_Mart/scripts.pory"
	.string "Full restoration of HP!\n"
# 87 "data/maps/SootopolisCity_Mart/scripts.pory"
	.string "Eradication of all status problems!\p"
# 88 "data/maps/SootopolisCity_Mart/scripts.pory"
	.string "It's truly an item of your dreams!$"
# 89 "data/maps/SootopolisCity_Mart/scripts.pory"

# 90 "data/maps/SootopolisCity_Mart/scripts.pory"
SootopolisCity_Mart_Text_DidSomethingAwaken:
# 91 "data/maps/SootopolisCity_Mart/scripts.pory"
	.string "This weather…\n"
# 92 "data/maps/SootopolisCity_Mart/scripts.pory"
	.string "Did something awaken?$"
