# 1 "data/maps/AlteringCave/scripts.pory"

# 2 "data/maps/AlteringCave/scripts.pory"
.set LOCALID_RED, 1
# 3 "data/maps/AlteringCave/scripts.pory"

# 4 "data/maps/AlteringCave/scripts.pory"

# 5 "data/maps/AlteringCave/scripts.pory"
AlteringCave_MapScripts::
# 6 "data/maps/AlteringCave/scripts.pory"
	map_script MAP_SCRIPT_ON_TRANSITION, AlteringCave_OnTransition
# 7 "data/maps/AlteringCave/scripts.pory"
	map_script MAP_SCRIPT_ON_LOAD, AlteringCave_Check_Red_Defeated
# 8 "data/maps/AlteringCave/scripts.pory"
	.byte 0
# 9 "data/maps/AlteringCave/scripts.pory"

# 10 "data/maps/AlteringCave/scripts.pory"
AlteringCave_OnTransition:
# 11 "data/maps/AlteringCave/scripts.pory"
	setflag FLAG_LANDMARK_ALTERING_CAVE
# 12 "data/maps/AlteringCave/scripts.pory"
	end
# 13 "data/maps/AlteringCave/scripts.pory"
AlteringCave_Check_Red_Defeated:
# 14 "data/maps/AlteringCave/scripts.pory"
	call_if_set FLAG_ALTERINGCAVE_RED_DEFEATED, AlteringCave_RemoveRed
# 15 "data/maps/AlteringCave/scripts.pory"
	return
# 16 "data/maps/AlteringCave/scripts.pory"
	
# 17 "data/maps/AlteringCave/scripts.pory"
AlteringCave_RemoveRed::
# 18 "data/maps/AlteringCave/scripts.pory"
	removeobject LOCALID_RED
# 19 "data/maps/AlteringCave/scripts.pory"
	return
# 20 "data/maps/AlteringCave/scripts.pory"

# 21 "data/maps/AlteringCave/scripts.pory"
AlteringCave_Red_Fight::
# 22 "data/maps/AlteringCave/scripts.pory"
	trainerbattle_single TRAINER_RED_ALTERING_CAVE,AlteringCave_Red_Speech, AlteringCave_Red_Speech_Defeat, AlteringCave_EventScript_Red_Disappear
# 23 "data/maps/AlteringCave/scripts.pory"
	release
# 24 "data/maps/AlteringCave/scripts.pory"
	end
# 25 "data/maps/AlteringCave/scripts.pory"
AlteringCave_EventScript_Red_Disappear::
# 26 "data/maps/AlteringCave/scripts.pory"
	fadescreen FADE_TO_BLACK
# 27 "data/maps/AlteringCave/scripts.pory"
	removeobject LOCALID_RED
# 28 "data/maps/AlteringCave/scripts.pory"
	fadescreen FADE_FROM_BLACK
# 29 "data/maps/AlteringCave/scripts.pory"
	setflag FLAG_ALTERINGCAVE_RED_DEFEATED
# 30 "data/maps/AlteringCave/scripts.pory"
	release
# 31 "data/maps/AlteringCave/scripts.pory"
	end
