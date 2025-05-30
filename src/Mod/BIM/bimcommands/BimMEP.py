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

"""BIM MEP Extension Commands"""

import FreeCAD
import FreeCADGui

QT_TRANSLATE_NOOP = FreeCAD.Qt.QT_TRANSLATE_NOOP
translate = FreeCAD.Qt.translate

PARAMS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/BIM")


class Arch_WaterPipe:
    """Command to create water pipes with MEP properties"""

    def GetResources(self):
        return {'Pixmap': 'Arch_Pipe',
                'MenuText': QT_TRANSLATE_NOOP("Arch_WaterPipe", "Water Pipe"),
                'Accel': "W, P",
                'ToolTip': QT_TRANSLATE_NOOP("Arch_WaterPipe", "Creates a water pipe with hydraulic calculations")}

    def IsActive(self):
        v = hasattr(FreeCADGui.getMainWindow().getActiveWindow(), "getSceneGraph")
        return v

    def Activated(self):
        s = FreeCADGui.Selection.getSelection()
        if s:
            for obj in s:
                if hasattr(obj, 'Shape'):
                    if len(obj.Shape.Wires) == 1:
                        FreeCAD.ActiveDocument.openTransaction(translate("Arch", "Create Water Pipe"))
                        FreeCADGui.addModule("Arch")
                        FreeCADGui.addModule("Draft")
                        FreeCADGui.doCommand(f"obj = Arch.makeWaterPipe(FreeCAD.ActiveDocument.{obj.Name})")
                        FreeCADGui.doCommand("Draft.autogroup(obj)")
                        FreeCAD.ActiveDocument.commitTransaction()
        else:
            FreeCAD.ActiveDocument.openTransaction(translate("Arch", "Create Water Pipe"))
            FreeCADGui.addModule("Arch")
            FreeCADGui.addModule("Draft")
            FreeCADGui.doCommand("obj = Arch.makeWaterPipe()")
            FreeCADGui.doCommand("Draft.autogroup(obj)")
            FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class Arch_SanitaryFixture:
    """Command to create sanitary fixtures"""

    def GetResources(self):
        return {'Pixmap': 'Arch_Equipment',
                'MenuText': QT_TRANSLATE_NOOP("Arch_SanitaryFixture", "Sanitary Fixture"),
                'Accel': "S, F",
                'ToolTip': QT_TRANSLATE_NOOP("Arch_SanitaryFixture", "Creates a sanitary fixture (sink, toilet, etc.)")}

    def IsActive(self):
        v = hasattr(FreeCADGui.getMainWindow().getActiveWindow(), "getSceneGraph")
        return v

    def Activated(self):
        s = FreeCADGui.Selection.getSelection()
        if s:
            for obj in s:
                if hasattr(obj, 'Shape'):
                    FreeCAD.ActiveDocument.openTransaction(translate("Arch", "Create Sanitary Fixture"))
                    FreeCADGui.addModule("Arch")
                    FreeCADGui.addModule("Draft")
                    FreeCADGui.doCommand(f"obj = Arch.makeSanitaryFixture(FreeCAD.ActiveDocument.{obj.Name})")
                    FreeCADGui.doCommand("Draft.autogroup(obj)")
                    FreeCAD.ActiveDocument.commitTransaction()
        else:
            FreeCAD.ActiveDocument.openTransaction(translate("Arch", "Create Sanitary Fixture"))
            FreeCADGui.addModule("Arch")
            FreeCADGui.addModule("Draft")
            FreeCADGui.doCommand("obj = Arch.makeSanitaryFixture()")
            FreeCADGui.doCommand("Draft.autogroup(obj)")
            FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class Arch_Valve:
    """Command to create valves and faucets"""

    def GetResources(self):
        return {'Pixmap': 'Arch_Equipment',
                'MenuText': QT_TRANSLATE_NOOP("Arch_Valve", "Valve/Faucet"),
                'Accel': "V, F",
                'ToolTip': QT_TRANSLATE_NOOP("Arch_Valve", "Creates a valve, faucet or tap")}

    def IsActive(self):
        v = hasattr(FreeCADGui.getMainWindow().getActiveWindow(), "getSceneGraph")
        return v

    def Activated(self):
        s = FreeCADGui.Selection.getSelection()
        if s:
            for obj in s:
                if hasattr(obj, 'Shape'):
                    FreeCAD.ActiveDocument.openTransaction(translate("Arch", "Create Valve"))
                    FreeCADGui.addModule("Arch")
                    FreeCADGui.addModule("Draft")
                    FreeCADGui.doCommand(f"obj = Arch.makeValve(FreeCAD.ActiveDocument.{obj.Name})")
                    FreeCADGui.doCommand("Draft.autogroup(obj)")
                    FreeCAD.ActiveDocument.commitTransaction()
        else:
            FreeCAD.ActiveDocument.openTransaction(translate("Arch", "Create Valve"))
            FreeCADGui.addModule("Arch")
            FreeCADGui.addModule("Draft")
            FreeCADGui.doCommand("obj = Arch.makeValve()")
            FreeCADGui.doCommand("Draft.autogroup(obj)")
            FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class Arch_MEPNetwork:
    """Command to create MEP networks"""

    def GetResources(self):
        return {'Pixmap': 'Arch_BuildingPart',
                'MenuText': QT_TRANSLATE_NOOP("Arch_MEPNetwork", "MEP Network"),
                'Accel': "M, N",
                'ToolTip': QT_TRANSLATE_NOOP("Arch_MEPNetwork", "Creates an MEP network from selected pipes and fixtures")}

    def IsActive(self):
        v = hasattr(FreeCADGui.getMainWindow().getActiveWindow(), "getSceneGraph")
        return v

    def Activated(self):
        import Draft
        s = FreeCADGui.Selection.getSelection()
        
        if not s:
            FreeCAD.Console.PrintError(translate("Arch", "Please select MEP objects to create network") + "\n")
            return
            
        # Classify selected objects
        pipes = []
        fixtures = []
        valves = []
        
        for obj in s:
            obj_type = getattr(obj.Proxy, 'Type', None) if hasattr(obj, 'Proxy') else None
            if obj_type == "WaterPipe" or Draft.getType(obj) == "Pipe":
                pipes.append(obj)
            elif obj_type == "SanitaryFixture":
                fixtures.append(obj)
            elif obj_type == "Valve":
                valves.append(obj)
        
        if not (pipes or fixtures or valves):
            FreeCAD.Console.PrintError(translate("Arch", "No valid MEP objects selected") + "\n")
            return
            
        FreeCAD.ActiveDocument.openTransaction(translate("Arch", "Create MEP Network"))
        FreeCADGui.addModule("Arch")
        
        # Build command string
        cmd_parts = []
        if pipes:
            pipe_names = "[" + ",".join([f"FreeCAD.ActiveDocument.{obj.Name}" for obj in pipes]) + "]"
            cmd_parts.append(f"pipes={pipe_names}")
        if fixtures:
            fixture_names = "[" + ",".join([f"FreeCAD.ActiveDocument.{obj.Name}" for obj in fixtures]) + "]"
            cmd_parts.append(f"fixtures={fixture_names}")
        if valves:
            valve_names = "[" + ",".join([f"FreeCAD.ActiveDocument.{obj.Name}" for obj in valves]) + "]"
            cmd_parts.append(f"valves={valve_names}")
            
        cmd = f"obj = Arch.makeMEPNetwork({','.join(cmd_parts)})"
        FreeCADGui.doCommand(cmd)
        
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class Arch_MEPHydraulicCalculation:
    """Command to perform hydraulic calculations on MEP networks"""

    def GetResources(self):
        return {'Pixmap': 'Arch_Schedule',
                'MenuText': QT_TRANSLATE_NOOP("Arch_MEPHydraulicCalculation", "Hydraulic Calculation"),
                'Accel': "H, C",
                'ToolTip': QT_TRANSLATE_NOOP("Arch_MEPHydraulicCalculation", "Performs hydraulic calculations on selected water pipes")}

    def IsActive(self):
        v = hasattr(FreeCADGui.getMainWindow().getActiveWindow(), "getSceneGraph")
        return v

    def Activated(self):
        import Draft
        s = FreeCADGui.Selection.getSelection()
        
        if not s:
            FreeCAD.Console.PrintError(translate("Arch", "Please select water pipes for calculation") + "\n")
            return
            
        calculated_pipes = []
        total_flow = 0.0
        total_pressure_loss = 0.0
        
        for obj in s:
            obj_type = getattr(obj.Proxy, 'Type', None) if hasattr(obj, 'Proxy') else None
            if obj_type == "WaterPipe":
                # Force recalculation
                if hasattr(obj.Proxy, 'calculateHydraulics'):
                    obj.Proxy.calculateHydraulics(obj)
                    calculated_pipes.append(obj)
                    total_flow += obj.FlowRate
                    total_pressure_loss += obj.PressureLoss
        
        if calculated_pipes:
            FreeCAD.Console.PrintMessage(f"Hydraulic calculation completed for {len(calculated_pipes)} pipes\n")
            FreeCAD.Console.PrintMessage(f"Total flow rate: {total_flow:.2f} L/min\n")
            FreeCAD.Console.PrintMessage(f"Total pressure loss: {total_pressure_loss:.4f} bar\n")
        else:
            FreeCAD.Console.PrintError(translate("Arch", "No water pipes selected") + "\n")


class Arch_MEPGroupCommand:
    """Group command for MEP tools"""

    def GetCommands(self):
        return tuple(['Arch_WaterPipe', 'Arch_SanitaryFixture', 'Arch_Valve', 'Arch_MEPNetwork', 'Arch_MEPHydraulicCalculation'])

    def GetResources(self):
        return {'MenuText': QT_TRANSLATE_NOOP("Arch_MEPTools", 'MEP Tools'),
                'ToolTip': QT_TRANSLATE_NOOP("Arch_MEPTools", 'MEP (Mechanical, Electrical, Plumbing) tools')}

    def IsActive(self):
        v = hasattr(FreeCADGui.getMainWindow().getActiveWindow(), "getSceneGraph")
        return v


# Register commands
FreeCADGui.addCommand('Arch_WaterPipe', Arch_WaterPipe())
FreeCADGui.addCommand('Arch_SanitaryFixture', Arch_SanitaryFixture())
FreeCADGui.addCommand('Arch_Valve', Arch_Valve())
FreeCADGui.addCommand('Arch_MEPNetwork', Arch_MEPNetwork())
FreeCADGui.addCommand('Arch_MEPHydraulicCalculation', Arch_MEPHydraulicCalculation())
FreeCADGui.addCommand('Arch_MEPTools', Arch_MEPGroupCommand()) 