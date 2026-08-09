AlteringCave_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, AlteringCave_OnTransition
	.byte 0

AlteringCave_OnTransition:
	setflag FLAG_LANDMARK_ALTERING_CAVE
	end

AlteringCave_EventScript_Red::
	trainerbattle_single TRAINER_RED_ALTERING_CAVE, AlteringCave_Text_RedIntro, AlteringCave_Text_RedDefeat, AlteringCave_EventScript_RedDefeated
	release
	end

AlteringCave_EventScript_RedDefeated::
	fadescreen FADE_TO_BLACK
	removeobject LOCALID_ALTERING_CAVE_RED
	setflag FLAG_ALTERINGCAVE_RED_DEFEATED
	fadescreen FADE_FROM_BLACK
	release
	end
