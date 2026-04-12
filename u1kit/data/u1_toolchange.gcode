; TODO: Replace with known-good Snapmaker Orca export
; This is a placeholder toolchange G-code template for the Snapmaker U1.
; The actual template should come from a verified Snapmaker Orca Slicer export.
;
; Snapmaker U1 toolchange sequence placeholder
G28 T ; Home toolchanger
T[next_extruder] ; Select next tool
G92 E0 ; Reset extruder position
