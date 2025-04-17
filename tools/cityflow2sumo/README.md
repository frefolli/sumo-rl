# Conversion of RoadNet Json to SUMO NetXML

## XML Road

```xml
<edge id="E8" from="J0" to="J16" priority="1" spreadType="center" shape="-20.87,48.49 -5.66,48.43">
  <lane id="E8_0" index="0" speed="13.89" length="15.21"/>
</edge>
```

## JSON Road

```json
{"id": "road_0_1_0",
 "points": [{"x": -300, "y": 0},
            {"x": 0, "y": 0}],
 "lanes": [{"width": 3, "maxSpeed": 11.111},
           {"width": 3, "maxSpeed": 11.111},
           {"width": 3, "maxSpeed": 11.111}],
 "startIntersection": "intersection_0_1",
 "endIntersection": "intersection_1_1"}
```

## XML Intersection

### Virtual := False

```xml
<junction id="J7" type="traffic_light" x="70.27" y="51.37" incLanes="E10_0 -E8_0" intLanes=":J7_0_0 :J7_1_0" >
  <request index="0" response="10" foes="10" cont="0"/>
  <request index="1" response="00" foes="01" cont="0"/>
</junction>
```

### Virtual := True

```xml
<junction id="J8" type="dead_end" x="39.07" y="-13.78" incLanes="-E11_0" intLanes=""/>

<tlLogic id="J0" type="static" programID="0" offset="0">
    <phase duration="42" state="rGGG"/>
    <phase duration="3"  state="ryGG"/>
    <phase duration="42" state="GrGG"/>
    <phase duration="3"  state="yrGG"/>
</tlLogic>
```


### JSON Virtual Intersection

```
{
  "id": "intersection_0_1",
    "point": {
      "x": -300,
      "y": 0
    },
    "width": 0,
    "roads": [
      "road_1_1_2",
    "road_0_1_0"
    ],
    "roadLinks": [],
    "trafficLight": {
      "roadLinkIndices": [],
      "lightphases": [
      {
        "time": 5,
        "availableRoadLinks": []
      },
      {
        "time": 30,
        "availableRoadLinks": []
      },
      {
        "time": 30,
        "availableRoadLinks": []
      },
      {
        "time": 30,
        "availableRoadLinks": []
      },
      {
        "time": 30,
        "availableRoadLinks": []
      },
      {
        "time": 30,
        "availableRoadLinks": []
      },
      {
        "time": 30,
        "availableRoadLinks": []
      },
      {
        "time": 30,
        "availableRoadLinks": []
      },
      {
        "time": 30,
        "availableRoadLinks": []
      }
      ]
    },
    "virtual": true
},
```

### JSON Concrete Intersection 

```
{
  "id": "intersection_1_1",
  "point": {
    "x": 0,
    "y": 0
  },
  "width": 11,
  "roads": [
    "road_0_1_0",
  "road_1_0_1",
  "road_2_1_2",
  "road_1_2_3",
  "road_1_1_0",
  "road_1_1_1",
  "road_1_1_2",
  "road_1_1_3"
  ],
  "roadLinks": [
  {
    "type": "go_straight",
    "startRoad": "road_0_1_0",
    "endRoad": "road_1_1_0",
    "direction": 0,
    "laneLinks": [
    {
      "startLaneIndex": 1,
      "endLaneIndex": 0,
      "points": [
      {
        "x": -11.0,
        "y": -4.5
      },
      {
        "x": -9.592,
        "y": -4.416
      },
      {
        "x": -7.656,
        "y": -4.188
      },
      {
        "x": -5.324,
        "y": -3.852
      },
      {
        "x": -2.7279999999999998,
        "y": -3.444
      },
      {
        "x": 0.0,
        "y": -3.0
      },
      {
        "x": 2.7279999999999998,
        "y": -2.556
      },
      {
        "x": 5.323999999999999,
        "y": -2.148
      },
      {
        "x": 7.655999999999999,
        "y": -1.811999999999999
      },
      {
        "x": 9.592,
        "y": -1.584
      },
      {
        "x": 11.0,
        "y": -1.5
      }
      ]
    },
    {
      "startLaneIndex": 1,
      "endLaneIndex": 1,
      "points": [
      {
        "x": -11.0,
        "y": -4.5
      },
      {
        "x": -9.592,
        "y": -4.5
      },
      {
        "x": -7.656,
        "y": -4.5
      },
      {
        "x": -5.324,
        "y": -4.5
      },
      {
        "x": -2.7279999999999998,
        "y": -4.5
      },
      {
        "x": 0.0,
        "y": -4.5
      },
      {
        "x": 2.7279999999999998,
        "y": -4.5
      },
      {
        "x": 5.323999999999999,
        "y": -4.5
      },
      {
        "x": 7.655999999999999,
        "y": -4.499999999999999
      },
      {
        "x": 9.592,
        "y": -4.5
      },
      {
        "x": 11.0,
        "y": -4.5
      }
      ]
    },
    {
      "startLaneIndex": 1,
      "endLaneIndex": 2,
      "points": [
      {
        "x": -11.0,
        "y": -4.5
      },
      {
        "x": -9.592,
        "y": -4.584
      },
      {
        "x": -7.656,
        "y": -4.812
      },
      {
        "x": -5.324,
        "y": -5.148
      },
      {
        "x": -2.7279999999999998,
        "y": -5.556
      },
      {
        "x": 0.0,
        "y": -6.0
      },
      {
        "x": 2.7279999999999998,
        "y": -6.444
      },
      {
        "x": 5.323999999999999,
        "y": -6.852
      },
      {
        "x": 7.655999999999999,
        "y": -7.187999999999999
      },
      {
        "x": 9.592,
        "y": -7.416
      },
      {
        "x": 11.0,
        "y": -7.5
      }
      ]
    }
    ]
  },
  ],
  "trafficLight": {
    "roadLinkIndices": [
      0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11
    ],
    "lightphases": [
    {
      "time": 5,
      "availableRoadLinks": [
        10,
      2,
      3,
      6
      ]
    },
    ]
  },
  "virtual": false
},
```

# Conversion of RoadNet Json to SUMO NetXML

## XML Route

```xml
<route id="r_0" edges="E3 E2.275"/>
<vehicle id="v_0" depart="0.00" route="r_0"/>
```

## JSON Route

```json
{"vehicle": {"length": 5.0,
             "width": 2.0,
             "maxPosAcc": 2.0,
             "maxNegAcc": 4.5,
             "usualPosAcc": 2.0,
             "usualNegAcc": 4.5,
             "minGap": 2.5,
             "maxSpeed": 11.111,
             "headwayTime": 2},
 "route": ["road_8_2_2", "road_7_2_3", "road_7_1_3"],
 "interval": 1.0,
 "startTime": 0,
 "endTime": 0}
```

# Warnings

- Always open and save the project with SUMO NetEdit before using it with the simulator to correct sorting errors.
- Since CityFlow simulator supports discontinued routes but SUMO simulator don't, I thought about using the `routecheck.py` tool of SUMO but it simply remove the broken route leaving untouched the vehicles which used it. So I tried to deal with these broken routes.
- CityFlow doesn't put priority in phases, so I assume that a lane has priority if is was big-Green (G) also in the previous step, otherwise is put small-Green (g). It's a fix that allows for always-green turns like the right-most one.
  - for now the broken routes are detected and excluded from files (as well as vehicles which use them)
- CityFlow doesn't have yellow phases, so i simply create a second phase afterwards with all small-greens (g) lowered to yellows and with `time = 5.00`.
