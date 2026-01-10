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

# 14 "data/maps/AlteringCave/scripts.pory"
AlteringCave_Check_Red_Defeated:
# 15 "data/maps/AlteringCave/scripts.pory"
	call_if_set FLAG_ALTERINGCAVE_RED_DEFEATED, AlteringCave_RemoveRed
# 16 "data/maps/AlteringCave/scripts.pory"
	return
# 17 "data/maps/AlteringCave/scripts.pory"
	
# 18 "data/maps/AlteringCave/scripts.pory"
AlteringCave_RemoveRed::
# 19 "data/maps/AlteringCave/scripts.pory"
	removeobject LOCALID_RED
# 20 "data/maps/AlteringCave/scripts.pory"
	return
# 21 "data/maps/AlteringCave/scripts.pory"

# 22 "data/maps/AlteringCave/scripts.pory"
AlteringCave_Red_Fight::
# 23 "data/maps/AlteringCave/scripts.pory"
	trainerbattle_single TRAINER_RED_ALTERING_CAVE,AlteringCave_Red_Speech, AlteringCave_Red_Speech_Defeat, AlteringCave_EventScript_Red_Disappear
# 24 "data/maps/AlteringCave/scripts.pory"
	release
# 25 "data/maps/AlteringCave/scripts.pory"
	end
# 26 "data/maps/AlteringCave/scripts.pory"
	
# 27 "data/maps/AlteringCave/scripts.pory"
AlteringCave_EventScript_Red_Disappear::
# 28 "data/maps/AlteringCave/scripts.pory"
	fadescreen FADE_TO_BLACK
# 29 "data/maps/AlteringCave/scripts.pory"
	removeobject LOCALID_RED
# 30 "data/maps/AlteringCave/scripts.pory"
	fadescreen FADE_FROM_BLACK
# 31 "data/maps/AlteringCave/scripts.pory"
	setflag FLAG_ALTERINGCAVE_RED_DEFEATED
# 32 "data/maps/AlteringCave/scripts.pory"
	release
# 33 "data/maps/AlteringCave/scripts.pory"
	end
