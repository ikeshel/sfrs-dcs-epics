# General Properties

This is for the settings document that will be automatized later for layout.

Monitor Resolution: 1920x1440
CS Studio Resolution: 1920x1280

## Main.bob features

Resolution: 1920x1280

## SCIFI features

### boardcard_SCIFI.bob

Card Resolution: 200x250

### BoardTemplate_SCIFI.bob

Resolution: 1820x1226
Margin top/bottom: 91.5
Margin right/left: 147.5

### SCIFI.bob

Resolution: 1825x1268

## PLSCI features

### boardcard_PLSCI.bob

Card Resolution: 350x331

### BoardTemplate_6_PLSCI.bob

Resolution: 1820x1226
Margin top/bottom: 0
Margin right/left: 375

### BoardTemplate_8_PLSCI.bob

Resolution: 1820x1226
Margin top/bottom: 0
Margin right/left: 0

### PLSCI.bob

Resolution: 1825x1268

## MUSIC features

### MUSIC_ONEBOX_TEMPLATE.bob

Card Resolution: 500x800

#### grupONE_FC properties

X position: 0
Y position: 0
Width: 500
Height: 800

##### rectLIMIT properties

X position: 0
Y position: 0
Width: 500
Height: 800

##### labeHEADER properties

PV= $(CHAMBER):MUSIC1:FC$(FIELD_CAGE)

X position: 0
Y position: 10
Width: 500
Height: 30

##### bobuHV_ENABLE properties

PV= SFRS:$(CHAMBER):MUSIC1:FC$(FIELD_CAGE):HV_ENABLE

X position: 25
Y position: 50
Width: 215
Height: 30

##### grupHV properties

X position: 10
Y position: 100
Width: 480
Height: 155

###### rectV_SET properties

X position: 0
Y position: 0
Width: 130
Height: 120

###### teupHV_V_SET properties

*invisible*

PV= SFRS:$(CHAMBER):MUSIC1:FC$(FIELD_CAGE):HV_V_SET

X position: 20
Y position: 20
Width: 90
Height: 30

###### teenHV_V_SET properties

PV= loc://HVSetEdit$(CHAMBER)FC$(FIELD_CAGE)(0)

X position: 20
Y position: 20
Width: 90
Height: 30

###### acbtV_SET properties

X position: 15
Y position: 70
Width: 100
Height: 30

###### limeHV_V_RBV properties

PV= SFRS:$(CHAMBER):MUSIC1:FC$(FIELD_CAGE):HV_V_RBV

X position: 140
Y position: 0
Width: 330
Height: 75

###### teupHV_V_RBV properties

PV= SFRS:$(CHAMBER):MUSIC1:FC$(FIELD_CAGE):HV_V_RBV

X position: 260
Y position: 0
Width: 90
Height: 30

###### limeHV_I_RBV properties

PV= SFRS:$(CHAMBER):MUSIC1:FC$(FIELD_CAGE):HV_I_RBV

X position: 140
Y position: 80
Width: 330
Height: 75

##### grupSTATUS properties

X position: 10
Y position: 265
Width: 480
Height: 75

###### rectSTATE properties

X position: 0
Y position: 0
Width: 480
Height: 75

###### labeSTATUS properties

X position: 15
Y position: 10
Width: 100
Height: 30

###### bymoSTATE properties

PV= SFRS:$(CHAMBER):MUSIC1:FC$(FIELD_CAGE):HV_STATE

X position: 150
Y position: 10
Width: 315
Height: 22

###### labeSTATE properties

X position: 15
Y position: 40
Width: 100
Height: 25

###### teupSTAT_NO properties

PV= SFRS:$(CHAMBER):MUSIC1:FC$(FIELD_CAGE):HV_STATE

X position: 150
Y position: 10
Width: 100
Height: 25

###### labeSTAT_LABEL properties

X position: 260
Y position: 40
Width: 200
Height: 25

##### dabrHV_PLOT properties

X position: 10
Y position: 350
Width: 480
Height: 440

### MUSIC_TWOFC_TEMPLATE.bob

Resolution: 1820x1226
Margin top/bottom: 213
Margin right/left: 360
Margin between FC: 100

#### MUSIC_FC1 embedded display properties

X position: 360
Y position: 213
Width: 500
Height: 800

#### MUSIC_FC2 embedded display properties

X position: 960
Y position: 213
Width: 500
Height: 800

### MUSIC_THREEFC_TEMPLATE.bob

Resolution: 1820x1226
Margin top/bottom: 213
Margin right/left: 60
Margin between FC: 100

#### MUSIC_FC1 embedded display properties

X position: 60
Y position: 213
Width: 500
Height: 800

#### MUSIC_FC2 embedded display properties

X position: 660
Y position: 213
Width: 500
Height: 800

#### MUSIC_FC3 embedded display properties

X position: 1260
Y position: 213
Width: 500
Height: 800

### MUSIC.bob

Resolution: 1825x1268

#### TabsMUSIC properties

X position: 0
Y position: 0
Width: 1825
Height: 1268

##### FMF1:MUSIC1 subtab properties

X position: 0
Y position: 0
Width: 1825
Height: 1268

###### FMF1:MUSIC1 embedded display properties

X position: 0
Y position: 2
Width: 1820
Height: 1226

##### FHF1:MUSIC1 subtab properties

X position: 0
Y position: 0
Width: 1825
Height: 1268

###### FHF1:MUSIC1 embedded display properties

X position: 0
Y position: 2
Width: 1820
Height: 1226