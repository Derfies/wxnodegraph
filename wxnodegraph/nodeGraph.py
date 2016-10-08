import math

import wx
import json

from constants import *
from wire import Wire
from node import Node
  

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
        node = Node( label, colour, rect=wx.Rect( pos.x, pos.y, 100, 100 ), ins=ins, outs=outs )
        nId = node.GetId()
        self.pdc.SetId( nId )
        node.Draw( self.pdc )
        self.pdc.SetIdBounds( nId, node.GetRect() )
        self.nodes[nId] = node
        return node

    def OnLeftDown( self, evt ):
        pnt = evt.GetPosition()
        winPnt = self.ConvertCoords( pnt )
        self.srcNode = self.HitTest( winPnt )
        if self.srcNode is not None:
            self.srcPlug = self.srcNode.HitTest( winPnt.x, winPnt.y )
            if self.srcPlug is not None:
                self.tmpWire = Wire( self.srcNode.GetRect().GetPosition() + self.srcPlug.pos, pnt, self.srcPlug.type )
        self.lastPnt = pnt

    def OnMotion( self, evt ):
        if not evt.LeftIsDown() or self.srcNode is None:
            return

        pnt = evt.GetPosition()
        winPnt = self.ConvertCoords( pnt )
        if self.srcPlug is None:
            dPnt = pnt - self.lastPnt
            r = self.pdc.GetIdBounds( self.srcNode.GetId() )
            self.pdc.TranslateId( self.srcNode.GetId(), dPnt[0], dPnt[1] )
            r2 = self.pdc.GetIdBounds( self.srcNode.GetId() )
            r = r.Union( r2 )
            self.OffsetRect( r )
            self.RefreshRect( r, False )
            self.lastPnt = pnt
            self.srcNode.SetRect( r2 )

            # Redraw wires
            for wire in self.srcNode.GetWires():
                pnt1 = wire.srcNode.GetRect().GetPosition() + wire.srcPlug.pos
                pnt2 = wire.dstNode.GetRect().GetPosition() + wire.dstPlug.pos
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
                dstPlug = dstNode.HitTest( winPnt.x, winPnt.y )
                if dstPlug is not None and self.srcPlug.type != dstPlug.type and self.srcNode.GetId() != dstNode.GetId():
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
        wire = Wire( srcNode.GetRect().GetPosition() + srcPlug.pos, dstNode.GetRect().GetPosition() + dstPlug.pos, srcPlug.type )
        wire.srcNode = srcNode
        wire.dstNode = dstNode
        wire.srcPlug = srcPlug
        wire.dstPlug = dstPlug
        srcNode._wires.append( wire )
        dstNode._wires.append( wire )

        for wire in srcNode._wires:
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
