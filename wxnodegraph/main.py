import math

import wx
import json


W = 2000
H = 2000
HIT_RADIUS = 5

PLUG_MARGIN = 6
PLUG_RADIUS = 4
PLUG_HIT_RADIUS = 10
PLUG_SPACING = 20
PLUG_TYPE_IN = 0
PLUG_TYPE_OUT = 1

ROUND_CORNER_RADIUS = 8

TITLE_INSET_X = 5
TITLE_INSET_Y = 1


WIRE_COLOUR = 'black'
WIRE_THICKNESS = 2


class Wire( object ):
    
    def __init__( self, pnt1, pnt2, dir_ ):
        self.pnt1 = pnt1
        self.pnt2 = pnt2
        self._idx = wx.NewId()
        self.dir = dir_

        # HAXXOR
        self.pen = wx.Pen( WIRE_COLOUR, WIRE_THICKNESS )

    def Draw( self, dc ):

        # HAXXOR for source / destination drawing direction.
        sign = 1
        if self.dir == PLUG_TYPE_IN:
            sign = -1

        pnts = []
        pnts.append( self.pnt1 )
        pnts.append( self.pnt1 + wx.Point( 10 * sign, 0 ) )
        pnts.append( self.pnt2 - wx.Point( 10 * sign, 0 ) )
        pnts.append( self.pnt2 )
        dc.SetPen( self.pen )
        dc.DrawSpline( pnts )
        '''
        # HAXXOR - New bezier curve.
        newPnts = []
        for point in bezier.bezier_curve_range( 40, pnts ):
            newPnts.append( point )

        #dc.DrawSpline( newPnts )
        lastPnt = newPnts[0]
        for pnt in newPnts:
            dc.DrawLine( lastPnt[0], lastPnt[1], pnt[0], pnt[1]) 
            lastPnt = pnt
        '''

    def GetRect( self ):
        minX = min( self.pnt1[0], self.pnt2[0] )
        minY = min( self.pnt1[1], self.pnt2[1] )
        size = self.pnt2 - self.pnt1
        rect = wx.Rect( minX - 10, minY, abs( size[0] ) + 20, abs( size[1] ) )
        return rect.Inflate( self.pen.GetWidth(), self.pen.GetWidth() )
        

class Plug( object ):
    
    def __init__( self, pos, radius, type_, node ):
        self.pos = wx.Point( pos[0], pos[1] )  # In node space
        self.radius = radius
        self.type = type_
        self.node = node

        self.wires = []

    def Draw( self, dc ):
        final = self.pos + self.node.pos
        dc.SetPen( wx.Pen( 'grey',style=wx.TRANSPARENT ) )
        dc.SetBrush( wx.Brush( 'black', wx.SOLID ) )
        dc.DrawCircle( final.x, final.y, self.radius )

    def HitTest( self, pos ):
        pnt = pos - self.pos
        dist = math.sqrt( math.pow( pnt.x, 2 ) + math.pow( pnt.y, 2 ) )
        if math.fabs( dist ) < PLUG_HIT_RADIUS:
            return True

    def CanConnect( self ):
        pass

    def Disconnect( self ):
        pass


class Node( object ):

    def __init__( self, label, pos, ins, outs, colour=None ):
        self.label = label
        self.pos = wx.Point( pos[0], pos[1] )

        self._idx = wx.NewId()
        self.size = (100, 100)
        self.ins = ins
        self.outs = outs
        self.selected = False
        self.drawn = False

        self._colour = colour or 'white'

        # HAXXOR
        self.plugs = []
        for i, in_ in enumerate( self.ins ):
            plug = Plug( (PLUG_MARGIN, 40 + PLUG_SPACING * i), PLUG_RADIUS, PLUG_TYPE_IN, self )
            self.plugs.append( plug )
        for i, out in enumerate( self.outs ):
            plug = Plug( (self.size[0] - PLUG_MARGIN - 1, 40 + PLUG_SPACING * i), PLUG_RADIUS, PLUG_TYPE_OUT, self )
            self.plugs.append( plug )

        self.wires = []

    def Draw( self, dc ):
        x, y = self.pos
        w, h = self.size
        dc.SetPen( wx.Pen( 'black', 1 ) )
        dc.SetBrush( wx.Brush( self._colour, wx.SOLID ) )
        dc.DrawRoundedRectangle( x, y, w, h, ROUND_CORNER_RADIUS )
        #dc.SetFont( self.GetFont().SetWeight( wx.BOLD ) )

        newFont = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        newFont.SetWeight(wx.BOLD)
        dc.SetFont( newFont )

        dc.DrawText( self.label, x + TITLE_INSET_X, y + TITLE_INSET_Y )

        # Draw ins / outs.
        for plug in self.plugs:
            plug.Draw( dc )

    def HitTest( self, pos ):
        for plug in self.plugs:
            if plug.HitTest( pos - self.pos ):
                return plug

    def UpdateRect( self, rect ):
        self.pos = rect.GetPosition()
        self.size = rect.GetSize()

    def GetRect( self ):
        return wx.Rect( self.pos[0], self.pos[1], self.size[0], self.size[1] )

    def SetColour( self, col ):
        self._colour = col


class NodeGraph( wx.ScrolledWindow ):
    def __init__(self, parent, id, log, size = wx.DefaultSize):
        wx.ScrolledWindow.__init__(self, parent, id, (0, 0), size=size, style=wx.SUNKEN_BORDER)

        self.nodes = {}
        self.srcNode = None
        self.srcPlug = None
        self.tmpWire = None

        self.maxWidth  = W
        self.maxHeight = H

        self.SetBackgroundColour( 'Grey' )
        self.SetVirtualSize( (self.maxWidth, self.maxHeight) )
        self.SetScrollRate( 20, 20 )
        
        # create a PseudoDC to record our drawing
        self.pdc = wx.PseudoDC()
        self.Bind( wx.EVT_PAINT, self.OnPaint )
        self.Bind( wx.EVT_ERASE_BACKGROUND, lambda x: None )
        self.Bind( wx.EVT_LEFT_DOWN, self.OnLeftDown )
        self.Bind( wx.EVT_MOTION, self.OnMotion )
        self.Bind( wx.EVT_LEFT_UP, self.OnLeftUp )

    def ConvertCoords( self, pnt ):
        xView, yView = self.GetViewStart()
        xDelta, yDelta = self.GetScrollPixelsPerUnit()
        return wx.Point(pnt[0] + (xView * xDelta), pnt[1] + (yView * yDelta))

    def OffsetRect(self, r):
        xView, yView = self.GetViewStart()
        xDelta, yDelta = self.GetScrollPixelsPerUnit()
        r.OffsetXY(-(xView*xDelta),-(yView*yDelta))

    def AppendItem( self, label, pos, ins, outs, colour=None ):
        node = Node( label, pos, ins, outs, colour )
        self.pdc.SetId( node._idx )
        node.Draw( self.pdc )
        self.pdc.SetIdBounds( node._idx, node.GetRect() )
        self.nodes[node._idx] = node
        return node

    def OnLeftDown( self, evt ):
        pnt = evt.GetPosition()
        winPnt = self.ConvertCoords( pnt )
        self.srcNode = self.HitTest( winPnt )
        if self.srcNode is not None:
            self.srcPlug = self.srcNode.HitTest( winPnt )
            if self.srcPlug is not None:
                self.tmpWire = Wire( self.srcNode.pos + self.srcPlug.pos, pnt, self.srcPlug.type )
        self.lastPnt = pnt

    def OnMotion( self, evt ):
        if not evt.LeftIsDown() or self.srcNode is None:
            return

        pnt = evt.GetPosition()
        winPnt = self.ConvertCoords( pnt )
        if self.srcPlug is None:
            dPnt = pnt - self.lastPnt
            r = self.pdc.GetIdBounds( self.srcNode._idx )
            self.pdc.TranslateId( self.srcNode._idx, dPnt[0], dPnt[1] )
            r2 = self.pdc.GetIdBounds( self.srcNode._idx )
            r = r.Union( r2 )
            self.OffsetRect( r )
            self.RefreshRect( r, False )
            self.lastPnt = pnt
            self.srcNode.UpdateRect( r2 )

            # Redraw wires
            for wire in self.srcNode.wires:
                pnt1 = wire.srcNode.pos + wire.srcPlug.pos
                pnt2 = wire.dstNode.pos + wire.dstPlug.pos
                self.DrawWire( wire, pnt1, pnt2 )

        elif self.tmpWire is not None:
            self.DrawWire( self.tmpWire, pnt2=winPnt )

    def OnLeftUp( self, evt ):

        # Attempt to make a connection.
        if self.srcNode is not None:
            pnt = evt.GetPosition()
            winPnt = self.ConvertCoords( pnt )
            dstNode = self.HitTest( winPnt )
            if dstNode is not None:
                dstPlug = dstNode.HitTest( winPnt )
                if dstPlug is not None and self.srcPlug.type != dstPlug.type and self.srcNode._idx != dstNode._idx:
                    self.ConnectNodes( self.srcNode, self.srcPlug, dstNode, dstPlug )

        # Erase the temp wire.
        if self.tmpWire is not None:
            rect = self.pdc.GetIdBounds( self.tmpWire._idx )
            self.pdc.RemoveId( self.tmpWire._idx ) 
            self.OffsetRect( rect )
            self.RefreshRect( rect, False )

        self.srcNode = None
        self.srcPlug = None
        self.tmpWire = None

    def HitTest( self, pt ):
        idxs = self.pdc.FindObjects( pt[0], pt[1], HIT_RADIUS )
        hits = [
            idx 
            for idx in idxs
            if idx in self.nodes
        ]
        return self.nodes[hits[0]] if hits else None

    def OnPaint(self, event):

        # Create a buffered paint DC.  It will create the real wx.PaintDC and 
        # then blit the bitmap to it when dc is deleted.
        dc = wx.BufferedPaintDC( self )
        dc = wx.GCDC( dc )

        # Use PrepateDC to set position correctly.
        self.PrepareDC( dc )

        # We need to clear the dc BEFORE calling PrepareDC.
        bg = wx.Brush( self.GetBackgroundColour() )
        dc.SetBackground( bg )
        dc.Clear()

        # Create a clipping rect from our position and size and the Update 
        # Region.
        xv, yv = self.GetViewStart()
        dx, dy = self.GetScrollPixelsPerUnit()
        x, y = (xv * dx, yv * dy)
        rgn = self.GetUpdateRegion()
        rgn.Offset( x, y )
        r = rgn.GetBox()

        # Draw to the dc using the calculated clipping rect.
        self.pdc.DrawToDCClipped( dc, r )

    def ConnectNodes( self, srcNode, srcPlug, dstNode, dstPlug ):
        wire = Wire( srcNode.pos + srcPlug.pos, dstNode.pos + dstPlug.pos, srcPlug.type )
        wire.srcNode = srcNode
        wire.dstNode = dstNode
        wire.srcPlug = srcPlug
        wire.dstPlug = dstPlug
        srcNode.wires.append( wire )
        dstNode.wires.append( wire )

        for wire in srcNode.wires:
            self.pdc.SetId( wire._idx )
            wire.Draw( self.pdc )
            self.pdc.SetIdBounds( wire._idx, wire.GetRect() )
            self.RefreshRect( wire.GetRect(), False )

    def DrawWire( self, wire, pnt1=None, pnt2=None ):
        rect1 = wire.GetRect()
        if pnt1 is not None:
            wire.pnt1 = pnt1
        if pnt2 is not None:
            wire.pnt2 = pnt2
        rect2 = wire.GetRect()
        rect = rect1.Union( rect2 )
        self.OffsetRect( rect )

        self.pdc.ClearId( wire._idx )
        self.pdc.SetId( wire._idx )
        wire.Draw( self.pdc )
        self.pdc.SetIdBounds( wire._idx, wire.GetRect() )
        self.RefreshRect( rect, False )

    def Load( self, filePath ):
        with open( filePath, 'r' ) as f:
            data = json.load( f )
            for nodeData in data:
                props = nodeData['properties']
                node = self.AppendItem( 
                    props['name'], 
                    wx.Point( props['x'], props['y'] ),
                    nodeData['ins'],
                    nodeData['outs'],
                    props['color']
                )
