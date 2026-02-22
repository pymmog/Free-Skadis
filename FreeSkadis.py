"""
Parametric IKEA Skådis Bin — FreeCAD Python Script
=========================================================

HOW TO USE:
  1. Run macro → "Params" VarSet + parametric "SkádisBin" created
  2. Edit values in VarSet (select "Params" → Properties panel)
  3. Right-click "SkádisBin" → Mark to recompute → Ctrl+Shift+R

HOOK SHAPE — L-bracket with drop stem (3 pieces):

  Side view (YZ plane):

         bin back        board (5mm)
             │         ←─────→
             │  ┌──────────────────┐
             │  │   TOP ARM (thin) │
             │  ├──┐               ├──┐
             │  │  │   (slot)      │  │ DROP
             │  │BA│               └──┘ STEM
             │  │CK│
             │  │  │
             │  └──┘
"""

import FreeCAD as App
import FreeCADGui as Gui
import Part

DEFAULTS = {
    "BIN_WIDTH":         (80.0,  "Bin",   "Bin outer width (mm)"),
    "BIN_HEIGHT":        (60.0,  "Bin",   "Bin outer height (mm)"),
    "BIN_DEPTH":         (50.0,  "Bin",   "Bin depth (mm)"),
    "SLOT_W":            ( 5.0,  "Board", "Skadis slot width (mm)"),
    "SLOT_H":            (15.0,  "Board", "Skadis slot height (mm)"),
    "GRID_X":            (20.0,  "Board", "Horizontal grid pitch (mm)"),
    "GRID_Y":            (20.0,  "Board", "Vertical grid pitch (mm)"),
    "BOARD_THICK":       ( 5.0,  "Board", "Skadis board thickness (mm)"),
    "BOARD_CLEAR":       ( 0.3,  "Board", "Clearance around board in slot gap (mm)"),
    "HOOK_WIDTH":        ( 3.0,  "Hook",  "Hook width — must fit through slot (mm)"),
    "TOP_ARM_HEIGHT":    ( 3.0,  "Hook",  "Top arm thickness in Z (mm)"),
    "BACK_ARM_THICK":    ( 2.0,  "Hook",  "Back arm depth in Y (mm)"),
    "BACK_ARM_HEIGHT":   ( 9.0,  "Hook",  "Back arm total height in Z (mm)"),
    "DROP_DEPTH":        ( 1.65, "Hook",  "Drop stem depth in Y (mm)"),
    "DROP_HEIGHT":       ( 2.0,  "Hook",  "Drop stem height in Z (mm)"),
    "HOOK_COLS":         ( 2.0,  "Hook",  "Number of hook columns"),
    "HOOK_ROWS":         ( 2.0,  "Hook",  "Desired hook rows per column (auto-clamped to fit)"),
}


def get_or_create_varset(doc):
    vs = doc.getObject("Params")
    if vs is None:
        vs = doc.addObject("App::VarSet", "Params")
        for name, (val, group, desc) in DEFAULTS.items():
            vs.addProperty("App::PropertyFloat", name, group, desc)
            setattr(vs, name, val)
        doc.recompute()
    return vs


def read_params(obj):
    p = {}
    for name, (default, _, _) in DEFAULTS.items():
        try:
            p[name] = float(getattr(obj, name))
        except Exception:
            p[name] = default
    return p


def make_hook(cx, cz, back_y, p):
    """
    3-piece hook at grid position (cx, cz).
    back_y = Y coordinate of the board front face.

    ① Back arm: Y = back_y - BACK_ARM_THICK .. back_y
                Z = cz - BACK_ARM_HEIGHT + TOP_ARM_HEIGHT .. cz + TOP_ARM_HEIGHT
    ② Top arm:  Y = back_y - BACK_ARM_THICK .. back_y + BOARD_THICK + BOARD_CLEAR + DROP_DEPTH
                Z = cz .. cz + TOP_ARM_HEIGHT
    ③ Drop stem: Y = back_y + BOARD_THICK + BOARD_CLEAR .. + DROP_DEPTH
                 Z = cz - DROP_HEIGHT .. cz
    """
    hw          = p["HOOK_WIDTH"]
    top_h       = p["TOP_ARM_HEIGHT"]
    back_thick  = p["BACK_ARM_THICK"]
    back_height = p["BACK_ARM_HEIGHT"]
    board_t     = p["BOARD_THICK"]
    board_clr   = p["BOARD_CLEAR"]
    drop_d      = p["DROP_DEPTH"]
    drop_h      = p["DROP_HEIGHT"]

    x0 = cx - hw / 2

    # Total top arm Y depth: back_arm + board gap + drop
    top_arm_depth = back_thick + board_t + board_clr + drop_d

    # Top of hook = cz + top_h, bottom of back arm = cz + top_h - back_height
    hook_top = cz + top_h

    # ① Back arm (vertical, in front of board)
    back_arm = Part.makeBox(
        hw, back_thick, back_height,
        App.Vector(x0, back_y - back_thick, hook_top - back_height)
    )

    # ② Top arm (horizontal thin bar, full depth)
    top_arm = Part.makeBox(
        hw, top_arm_depth, top_h,
        App.Vector(x0, back_y - back_thick, cz)
    )

    # ③ Drop stem (behind board, hangs down)
    drop_y_start = back_y + board_t + board_clr
    drop_stem = Part.makeBox(
        hw, drop_d, drop_h,
        App.Vector(x0, drop_y_start, cz - drop_h)
    )

    return back_arm.fuse(top_arm).fuse(drop_stem)


def hook_positions(p):
    W  = p["BIN_WIDTH"]
    H  = p["BIN_HEIGHT"]
    gx = p["GRID_X"]
    gy = p["GRID_Y"]
    back_height = p["BACK_ARM_HEIGHT"]
    top_h       = p["TOP_ARM_HEIGHT"]
    drop_h      = p["DROP_HEIGHT"]

    n_cols = max(1, int(p["HOOK_COLS"]))
    n_rows = max(1, int(p["HOOK_ROWS"]))

    # ── Center columns horizontally ──
    if n_cols == 1:
        col_xs = [W / 2.0]
    else:
        span = (n_cols - 1) * gx
        x0 = (W - span) / 2.0
        col_xs = [x0 + j * gx for j in range(n_cols)]

    # ── Vertical spacing: rows are 2*GRID_Y apart (Skadis stagger) ──
    row_spacing = gy * 2
    # Each hook needs this Z clearance:
    hook_extent_up   = top_h           # above cz
    hook_extent_down = back_height - top_h + drop_h  # below cz

    # Total Z span needed for n rows
    total_rows_span = (n_rows - 1) * row_spacing + hook_extent_up + hook_extent_down

    # Auto-clamp: reduce rows until they fit
    actual_rows = n_rows
    while actual_rows > 1:
        span_needed = (actual_rows - 1) * row_spacing + hook_extent_up + hook_extent_down
        if span_needed <= H:
            break
        actual_rows -= 1

    total_span = (actual_rows - 1) * row_spacing + hook_extent_up + hook_extent_down

    # Center rows vertically: find cz of the topmost row
    # top of topmost hook  = cz_top + hook_extent_up
    # bottom of lowest hook = cz_top - (actual_rows-1)*row_spacing - hook_extent_down + top_h
    # We want these centred in H:
    #   margin = (H - total_span) / 2
    #   cz_top = H - margin - hook_extent_up
    margin = (H - total_span) / 2.0
    cz_top = H - margin - hook_extent_up

    # ── Stagger: odd columns offset by GRID_Y ──
    positions = []
    for j, cx in enumerate(col_xs):
        stagger = gy if (j % 2 != 0) else 0.0
        for r in range(actual_rows):
            cz = cz_top - r * row_spacing + stagger

            # Safety: skip if hook doesn't fit vertically
            if cz + hook_extent_up > H or cz - (back_height - top_h + drop_h) < 0:
                continue

            positions.append((cx, cz))

    return positions



def build_shape(p):
    W, H, D = p["BIN_WIDTH"], p["BIN_HEIGHT"], p["BIN_DEPTH"]
    result = Part.makeBox(W, D, H, App.Vector(0, 0, 0))
    back_y = D
    for (cx, cz) in hook_positions(p):
        hook = make_hook(cx, cz, back_y, p)
        result = result.fuse(hook)
    return result.removeSplitter()


class SkádisBinProxy:
    Type = "SkádisBin"

    def __init__(self, obj):
        obj.Proxy = self
        for name, (val, group, desc) in DEFAULTS.items():
            if not hasattr(obj, name):
                obj.addProperty("App::PropertyFloat", name, group, desc)
                setattr(obj, name, val)

    def execute(self, obj):
        p = read_params(obj)
        try:
            obj.Shape = build_shape(p)
        except Exception as e:
            App.Console.PrintError(f"SkádisBin build error: {e}\n")

    def onChanged(self, obj, prop):
        pass

    def __getstate__(self):
        return self.Type

    def __setstate__(self, state):
        self.Type = state if state else "SkádisBin"


class ViewProviderSkádisBin:
    def __init__(self, vobj):
        vobj.Proxy = self
    def attach(self, vobj):
        self.Object = vobj.Object
    def getIcon(self):
        return ""
    def __getstate__(self):
        return None
    def __setstate__(self, state):
        return None


# ── MAIN ──
doc = App.activeDocument()
if doc is None:
    doc = App.newDocument("SkádisBin")

vs = get_or_create_varset(doc)

# Remove old objects
for name in ("SkádisBin", "SkádisBinBody"):
    old = doc.getObject(name)
    if old is not None:
        doc.removeObject(name)

# Create parametric Part
obj = doc.addObject("Part::FeaturePython", "SkádisBin")
SkádisBinProxy(obj)
ViewProviderSkádisBin(obj.ViewObject)
obj.Label = "SkádisBin"

for name in DEFAULTS:
    obj.setExpression(name, f"Params.{name}")

doc.recompute()

# Wrap in a PartDesign Body
body = doc.addObject("PartDesign::Body", "SkádisBinBody")
body.BaseFeature = obj
obj.Visibility = False
body.Label = "SkádisBin Body"

doc.recompute()

try:
    Gui.activeDocument().activeView().viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")
except Exception:
    pass

p = read_params(obj)
hooks = hook_positions(p)
print(f"Built: {p['BIN_WIDTH']:.0f}×{p['BIN_HEIGHT']:.0f}×{p['BIN_DEPTH']:.0f}mm | {len(hooks)} hooks")
print("→ 'SkádisBin Body' is a PartDesign::Body — add Fillets, Pockets, Pads etc.")
print("→ Edit 'Params' VarSet → Mark to recompute → Ctrl+Shift+R")
