;===== date: 20251213=====================
; Change Tool[previous_extruder] -> Tool[next_extruder] (layer [layer_num])
{
local max_speed_toolchange = 350.0;
local wait_for_extruder_temp = true;
position[2] = position[2] + 2.0;
local speed_toolchange = max_speed_toolchange;
if travel_speed < max_speed_toolchange then
      speed_toolchange = travel_speed;
endif
"G91
G1 Z1.5 F1800
G90
";
"G1 F" + (speed_toolchange * 60) + "
";
if wait_for_extruder_temp and not((layer_num < 0) and (next_extruder == initial_tool)) then
      "
";
      "; " + layer_num + "
";
      if layer_num == 0 then
            "M109 S" + first_layer_temperature[next_extruder] + " T" + next_extruder + "
";
      else
            "M109 S" + temperature[next_extruder] + " T" + next_extruder + "
";
      endif
endif
"M400" + "
";
"T" + next_extruder + "
";
if filament_type[next_extruder] == "PVA" then
"SET_VELOCITY_LIMIT ACCEL=3000
";
else
endif
if previous_extruder != next_extruder and initial_extruder != next_extruder then
"SM_PRINT_PREEXTRUDE_FILAMENT INDEX=" + next_extruder + "
";
endif
"G90
";
}
