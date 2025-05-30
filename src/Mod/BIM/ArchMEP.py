# SPDX-License-Identifier: LGPL-2.1-or-later

# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2024 MeliCAD MEP Extension                             *
# *                                                                         *
# *   This file is part of FreeCAD.                                         *
# *                                                                         *
# *   FreeCAD is free software: you can redistribute it and/or modify it    *
# *   under the terms of the GNU Lesser General Public License as           *
# *   published by the Free Software Foundation, either version 2.1 of the  *
# *   License, or (at your option) any later version.                       *
# *                                                                         *
# *   FreeCAD is distributed in the hope that it will be useful, but        *
# *   WITHOUT ANY WARRANTY; without even the implied warranty of            *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU      *
# *   Lesser General Public License for more details.                       *
# *                                                                         *
# *   You should have received a copy of the GNU Lesser General Public      *
# *   License along with FreeCAD. If not, see                               *
# *   <https://www.gnu.org/licenses/>.                                      *
# *                                                                         *
# ***************************************************************************

__title__ = "FreeCAD MEP Extension"
__author__ = "MeliCAD Team"
__url__ = "https://www.freecad.org"

## @package ArchMEP
#  \ingroup ARCH
#  \brief MEP (Mechanical, Electrical, Plumbing) extension for FreeCAD BIM
#
#  This module extends the existing Arch components with specialized MEP functionality
#  for water supply systems, sanitary fixtures, valves, and hydraulic calculations

import FreeCAD
import ArchComponent
import ArchPipe
import ArchEquipment
import ArchIFC
import math

from draftutils import params

if FreeCAD.GuiUp:
    from PySide.QtCore import QT_TRANSLATE_NOOP
    import FreeCADGui
    from draftutils.translate import translate
else:
    # \cond
    def translate(ctxt,txt):
        return txt
    def QT_TRANSLATE_NOOP(ctxt,txt):
        return txt
    # \endcond


class _ArchWaterPipe(ArchPipe._ArchPipe):
    """
    Extended water pipe object with hydraulic calculations and MEP properties.
    Inherits from ArchPipe._ArchPipe to maintain compatibility.
    """

    def __init__(self, obj):
        ArchPipe._ArchPipe.__init__(self, obj)
        self.setMEPProperties(obj)
        obj.IfcType = "Pipe Segment"

    def setMEPProperties(self, obj):
        """Add MEP-specific properties to the water pipe"""
        pl = obj.PropertiesList
        
        # Hydraulic Properties
        if not "FlowRate" in pl:
            obj.addProperty("App::PropertyFloat", "FlowRate", "MEP Hydraulics", 
                          QT_TRANSLATE_NOOP("App::Property","Flow rate in liters/minute"), locked=True)
            obj.FlowRate = 0.0
            
        if not "Pressure" in pl:
            obj.addProperty("App::PropertyFloat", "Pressure", "MEP Hydraulics",
                          QT_TRANSLATE_NOOP("App::Property","Pressure in bar"), locked=True)
            obj.Pressure = 2.5  # Default water pressure
            
        if not "PressureLoss" in pl:
            obj.addProperty("App::PropertyFloat", "PressureLoss", "MEP Hydraulics",
                          QT_TRANSLATE_NOOP("App::Property","Calculated pressure loss in bar"), locked=True)
            obj.setEditorMode("PressureLoss", 1)  # Read-only
            
        if not "Velocity" in pl:
            obj.addProperty("App::PropertyFloat", "Velocity", "MEP Hydraulics",
                          QT_TRANSLATE_NOOP("App::Property","Water velocity in m/s"), locked=True)
            obj.setEditorMode("Velocity", 1)  # Read-only
            
        # MEP Classification
        if not "SystemType" in pl:
            obj.addProperty("App::PropertyEnumeration", "SystemType", "MEP System",
                          QT_TRANSLATE_NOOP("App::Property","Type of water system"), locked=True)
            obj.SystemType = ["Cold Water Supply", "Hot Water Supply", "Waste Water", "Rain Water", "Gas"]
            obj.SystemType = "Cold Water Supply"
            
        if not "PipeMaterial" in pl:
            obj.addProperty("App::PropertyEnumeration", "PipeMaterial", "MEP System",
                          QT_TRANSLATE_NOOP("App::Property","Pipe material specification"), locked=True)
            obj.PipeMaterial = ["Copper", "PVC", "PEX", "Steel", "Cast Iron", "HDPE"]
            obj.PipeMaterial = "Copper"
            
        if not "RoughnessCoeff" in pl:
            obj.addProperty("App::PropertyFloat", "RoughnessCoeff", "MEP System",
                          QT_TRANSLATE_NOOP("App::Property","Pipe roughness coefficient"), locked=True)
            obj.RoughnessCoeff = 0.0015  # Default for copper
            
        if not "InsulationThickness" in pl:
            obj.addProperty("App::PropertyLength", "InsulationThickness", "MEP System",
                          QT_TRANSLATE_NOOP("App::Property","Insulation thickness"), locked=True)
            
        # MEP Connections
        if not "ConnectedFixtures" in pl:
            obj.addProperty("App::PropertyLinkList", "ConnectedFixtures", "MEP Connections",
                          QT_TRANSLATE_NOOP("App::Property","Connected sanitary fixtures"), locked=True)
            
        if not "ConnectedValves" in pl:
            obj.addProperty("App::PropertyLinkList", "ConnectedValves", "MEP Connections",
                          QT_TRANSLATE_NOOP("App::Property","Connected valves and fittings"), locked=True)

        self.Type = "WaterPipe"

    def onChanged(self, obj, prop):
        """Override onChanged to add hydraulic calculations"""
        ArchPipe._ArchPipe.onChanged(self, obj, prop)
        
        # Update material properties when material changes
        if prop == "PipeMaterial":
            self.updateMaterialProperties(obj)
            
        # Recalculate hydraulics when relevant properties change
        if prop in ["FlowRate", "Diameter", "Length", "PipeMaterial", "RoughnessCoeff"]:
            self.calculateHydraulics(obj)

    def updateMaterialProperties(self, obj):
        """Update roughness coefficient based on material"""
        material_roughness = {
            "Copper": 0.0015,
            "PVC": 0.0001,
            "PEX": 0.0001,
            "Steel": 0.045,
            "Cast Iron": 0.25,
            "HDPE": 0.0001
        }
        obj.RoughnessCoeff = material_roughness.get(obj.PipeMaterial, 0.0015)

    def calculateHydraulics(self, obj):
        """Calculate hydraulic parameters using Darcy-Weisbach equation"""
        if obj.FlowRate == 0 or obj.Diameter.Value == 0:
            return
            
        # Convert units
        flow_m3s = obj.FlowRate / 60000.0  # L/min to m³/s
        diameter_m = obj.Diameter.Value / 1000.0  # mm to m
        length_m = obj.Length.Value / 1000.0  # mm to m
        
        # Calculate cross-sectional area
        area = math.pi * (diameter_m / 2) ** 2
        
        # Calculate velocity
        velocity = flow_m3s / area if area > 0 else 0
        obj.Velocity = velocity
        
        # Calculate pressure loss using Darcy-Weisbach equation
        # ΔP = f * (L/D) * (ρ * v²) / 2
        # Simplified friction factor for turbulent flow
        reynolds = velocity * diameter_m / 1.004e-6  # Kinematic viscosity of water at 20°C
        
        if reynolds > 0:
            # Colebrook-White approximation for friction factor
            friction_factor = 0.25 / (math.log10(obj.RoughnessCoeff / (3.7 * diameter_m) + 5.74 / (reynolds ** 0.9))) ** 2
            
            # Pressure loss in Pascal, converted to bar
            pressure_loss_pa = friction_factor * (length_m / diameter_m) * (1000 * velocity ** 2) / 2
            obj.PressureLoss = pressure_loss_pa / 100000.0  # Pa to bar
        else:
            obj.PressureLoss = 0.0


class _ArchSanitaryFixture(ArchEquipment._ArchEquipment):
    """
    Sanitary fixture object that extends ArchEquipment for bathroom and kitchen fixtures.
    """

    def __init__(self, obj):
        ArchEquipment._ArchEquipment.__init__(self, obj)
        self.setFixtureProperties(obj)
        obj.IfcType = "Sanitary Terminal"

    def setFixtureProperties(self, obj):
        """Add fixture-specific properties"""
        pl = obj.PropertiesList
        
        # Fixture Classification
        if not "FixtureType" in pl:
            obj.addProperty("App::PropertyEnumeration", "FixtureType", "Fixture",
                          QT_TRANSLATE_NOOP("App::Property","Type of sanitary fixture"), locked=True)
            obj.FixtureType = ["Sink", "Wash Hand Basin", "Toilet Pan", "Urinal", "Bath", "Shower", "Bidet"]
            obj.FixtureType = "Sink"
            
        if not "FixtureUnits" in pl:
            obj.addProperty("App::PropertyFloat", "FixtureUnits", "Fixture",
                          QT_TRANSLATE_NOOP("App::Property","Fixture units for load calculation"), locked=True)
            obj.FixtureUnits = 1.0
            
        if not "FlowRate" in pl:
            obj.addProperty("App::PropertyFloat", "FlowRate", "Fixture",
                          QT_TRANSLATE_NOOP("App::Property","Required flow rate in L/min"), locked=True)
            obj.FlowRate = 6.0  # Standard sink flow rate
            
        # Water Connections
        if not "ColdWaterConnection" in pl:
            obj.addProperty("App::PropertyLink", "ColdWaterConnection", "Connections",
                          QT_TRANSLATE_NOOP("App::Property","Cold water supply connection"), locked=True)
            
        if not "HotWaterConnection" in pl:
            obj.addProperty("App::PropertyLink", "HotWaterConnection", "Connections",
                          QT_TRANSLATE_NOOP("App::Property","Hot water supply connection"), locked=True)
            
        if not "DrainConnection" in pl:
            obj.addProperty("App::PropertyLink", "DrainConnection", "Connections",
                          QT_TRANSLATE_NOOP("App::Property","Drain water connection"), locked=True)
            
        # Installation Properties
        if not "WallMounted" in pl:
            obj.addProperty("App::PropertyBool", "WallMounted", "Installation",
                          QT_TRANSLATE_NOOP("App::Property","Whether fixture is wall mounted"), locked=True)
            obj.WallMounted = True
            
        if not "InstallationHeight" in pl:
            obj.addProperty("App::PropertyLength", "InstallationHeight", "Installation",
                          QT_TRANSLATE_NOOP("App::Property","Installation height from floor"), locked=True)
            obj.InstallationHeight = 850  # Standard height in mm

        self.Type = "SanitaryFixture"

    def onChanged(self, obj, prop):
        """Update fixture properties based on type"""
        ArchEquipment._ArchEquipment.onChanged(self, obj, prop)
        
        if prop == "FixtureType":
            self.updateFixtureDefaults(obj)

    def updateFixtureDefaults(self, obj):
        """Update default values based on fixture type"""
        fixture_defaults = {
            "Sink": {"FlowRate": 6.0, "FixtureUnits": 1.5, "InstallationHeight": 850},
            "Wash Hand Basin": {"FlowRate": 4.0, "FixtureUnits": 1.0, "InstallationHeight": 800},
            "Toilet Pan": {"FlowRate": 0.0, "FixtureUnits": 4.0, "InstallationHeight": 400},
            "Urinal": {"FlowRate": 0.0, "FixtureUnits": 2.0, "InstallationHeight": 600},
            "Bath": {"FlowRate": 12.0, "FixtureUnits": 3.0, "InstallationHeight": 0},
            "Shower": {"FlowRate": 9.0, "FixtureUnits": 2.0, "InstallationHeight": 2100},
            "Bidet": {"FlowRate": 4.0, "FixtureUnits": 1.0, "InstallationHeight": 400}
        }
        
        defaults = fixture_defaults.get(obj.FixtureType, {})
        obj.FlowRate = defaults.get("FlowRate", 6.0)
        obj.FixtureUnits = defaults.get("FixtureUnits", 1.0)
        obj.InstallationHeight = defaults.get("InstallationHeight", 850)


class _ArchValve(ArchComponent.Component):
    """
    Valve component for MEP systems including faucets, taps, and control valves.
    """

    def __init__(self, obj):
        ArchComponent.Component.__init__(self, obj)
        self.setValveProperties(obj)
        obj.IfcType = "Valve"

    def setValveProperties(self, obj):
        """Add valve-specific properties"""
        pl = obj.PropertiesList
        
        # Valve Classification
        if not "ValveType" in pl:
            obj.addProperty("App::PropertyEnumeration", "ValveType", "Valve",
                          QT_TRANSLATE_NOOP("App::Property","Type of valve"), locked=True)
            obj.ValveType = ["Faucet", "Stop Cock", "Check Valve", "Pressure Relief", "Mixing Valve", "Gas Tap", "Isolating"]
            obj.ValveType = "Faucet"
            
        if not "NominalDiameter" in pl:
            obj.addProperty("App::PropertyLength", "NominalDiameter", "Valve",
                          QT_TRANSLATE_NOOP("App::Property","Nominal diameter of valve"), locked=True)
            obj.NominalDiameter = 15  # 15mm standard
            
        if not "WorkingPressure" in pl:
            obj.addProperty("App::PropertyFloat", "WorkingPressure", "Valve",
                          QT_TRANSLATE_NOOP("App::Property","Maximum working pressure in bar"), locked=True)
            obj.WorkingPressure = 10.0
            
        if not "FlowCoefficient" in pl:
            obj.addProperty("App::PropertyFloat", "FlowCoefficient", "Valve",
                          QT_TRANSLATE_NOOP("App::Property","Valve flow coefficient (Kv)"), locked=True)
            obj.FlowCoefficient = 1.0
            
        # Control Properties  
        if not "IsMotorized" in pl:
            obj.addProperty("App::PropertyBool", "IsMotorized", "Control",
                          QT_TRANSLATE_NOOP("App::Property","Whether valve is motorized"), locked=True)
            obj.IsMotorized = False
            
        if not "ControlSignal" in pl:
            obj.addProperty("App::PropertyEnumeration", "ControlSignal", "Control",
                          QT_TRANSLATE_NOOP("App::Property","Control signal type"), locked=True)
            obj.ControlSignal = ["Manual", "24V DC", "230V AC", "0-10V", "4-20mA"]
            obj.ControlSignal = "Manual"
            
        # Connection Properties
        if not "InletConnection" in pl:
            obj.addProperty("App::PropertyLink", "InletConnection", "Connections",
                          QT_TRANSLATE_NOOP("App::Property","Inlet pipe connection"), locked=True)
            
        if not "OutletConnection" in pl:
            obj.addProperty("App::PropertyLink", "OutletConnection", "Connections",
                          QT_TRANSLATE_NOOP("App::Property","Outlet pipe connection"), locked=True)

        self.Type = "Valve"

    def execute(self, obj):
        """Create valve geometry"""
        if self.clone(obj):
            return
            
        # Create simple valve representation if no base shape
        if not obj.Base:
            import Part
            # Create a cylinder for valve body
            diameter = obj.NominalDiameter.Value
            height = diameter * 1.5
            
            valve_body = Part.makeCylinder(diameter/2, height)
            
            # Add simple handle for manual valves
            if obj.ControlSignal == "Manual":
                handle = Part.makeBox(diameter * 0.3, diameter * 2, diameter * 0.2)
                handle.translate(FreeCAD.Vector(-diameter * 0.15, -diameter, height))
                valve_body = valve_body.fuse(handle)
            
            obj.Shape = valve_body
        else:
            ArchComponent.Component.execute(self, obj)


# View Providers
class _ViewProviderWaterPipe:
    """View provider for water pipes with color coding by system type"""
    
    def __init__(self, vobj):
        vobj.Proxy = self
        
    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        
    def updateData(self, obj, prop):
        if prop == "SystemType":
            self.updateSystemColor(obj)
            
    def updateSystemColor(self, obj):
        """Color code pipes by system type"""
        if FreeCAD.GuiUp:
            color_map = {
                "Cold Water Supply": (0.0, 0.0, 1.0),    # Blue
                "Hot Water Supply": (1.0, 0.0, 0.0),     # Red  
                "Waste Water": (0.5, 0.3, 0.1),          # Brown
                "Rain Water": (0.0, 1.0, 1.0),           # Cyan
                "Gas": (1.0, 1.0, 0.0)                   # Yellow
            }
            color = color_map.get(obj.SystemType, (0.7, 0.7, 0.7))  # Default gray
            obj.ViewObject.LineColor = color
            obj.ViewObject.ShapeColor = color


class _ViewProviderSanitaryFixture:
    """View provider for sanitary fixtures"""
    
    def __init__(self, vobj):
        vobj.Proxy = self
        
    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object


class _ViewProviderValve:
    """View provider for valves with icon representation"""
    
    def __init__(self, vobj):
        vobj.Proxy = self
        
    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object 