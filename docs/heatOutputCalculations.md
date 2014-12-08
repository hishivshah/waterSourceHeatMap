### Heat Output (MW)
h = Q \* ρ \* c<sub>p</sub> \* ΔT \* 10<sup>-6</sup>

h = heat output (MW)  
Q = river flow (m<sup>3</sup> s<sup>-1</sup>)  
ρ = water density (kg m<sup>-3</sup>)  
c<sub>p</sub> = specific heat of water (J kg<sup>-1</sup> K<sup>-1</sup>)  
ΔT = change in water temperature (K)  
10<sup>-6</sup> = unit conversion from Watts (W) to MegaWatts (MW)

assuming [ρ = 1000][1], [c<sub>p</sub> = 4180][2], and [ΔT = 2][3]:

**h = Q * 8.36**

### Maximum Heat Output (MW)
h<sub>max</sub> = l \* P<sub>max</sub> \* d<sup>-1</sup>

h<sub>max</sub> = maximum heat output (MW)  
l = river length (m)  
P<sub>max</sub> = maximum capacity of heat pump (MW)  
d<sup>-1</sup> = minimum distance between heat pumps (m)

assuming [P<sub>max</sub> = 20][3], [d = 1000][3]:

**h<sub>max</sub> = l \* 0.02**

### Heat Energy Produced (GWh)
E<sub>t</sub> = min(h, h<sub>max</sub>) \* t \* 3600<sup>-1</sup> \* 10<sup>-3</sup>

E<sub>t</sub> = heat energy produced during time period t (GWh)  
t = time period (s)  
3600<sup>-1</sup> = unit conversion from MegaJoules (MJ) to MegaWatthours (MWh)  
10<sup>-3</sup> = unit conversion from MegaWatthours (MWh) to GigaWatthours (GWh)

assuming t = 1 month = 2628000s:

**E<sub>t</sub> = min(h, h<sub>max</sub>) \* 0.73**


[1]: http://www.wolframalpha.com/input/?i=density+of+water
[2]: http://www.wolframalpha.com/input/?i=specific+heat+of+water
[3]: https://www.gov.uk/government/uploads/system/uploads/attachment_data/file/342353/High_Level_Water_Source_Heat_Map-Context_8Aug__3_.pdf
