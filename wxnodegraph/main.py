import math

import wx


W = 2000
H = 2000
hitradius = 5


PLUG_RADIUS = 10
PLUG_SPACING = 20
PLUG_TYPE_IN = 0
PLUG_TYPE_OUT = 0


class PdcRect( object ):
    pass


class Wire( object ):
    
    def __init__( self, node1, plug1, node2, plug2 ):
        self.node1 = node1
        self.plug1 = plug1
        self.node2 = node2
        self.plug2 = plug2
        self._idx = wx.NewId()

    def Draw( self, dc ):
        pnts = []

        #pos = wx.Point( self.pos[0], self.pos[1] )
        #nPos = wx.Point( self.node.pos[0], self.node.pos[1] )

        pnt1 = self.node1.pos + self.plug1.pos
        pnt2 = self.node1.pos + self.plug1.pos

        pnts.append( pnt1 )
        pnts.append( pnt1 + wx.Point( 20, 0 ) )
        pnts.append( pnt2 - wx.Point( -20, 0 ) )
        pnts.append( pnt2 )
        dc.DrawSpline( pnts )


class Plug( object ):
    
    def __init__( self, pos, radius, type_, node ):
        self.pos = wx.Point( pos[0], pos[1] )  # In node space
        self.radius = radius
        self.type = type_
        self.node = node

    def Draw( self, dc ):
        #pos = wx.Point( self.pos[0], self.pos[1] )
       # nPos = wx.Point( self.node.pos[0], self.node.pos[1] )
        final = self.pos + self.node.pos
        dc.DrawCircle( final.x, final.y, self.radius )

    def HitTest( self, pos ):
        pnt = pos - self.pos
        dist = math.sqrt( math.pow( pnt.x, 2 ) + math.pow( pnt.y, 2 ) )
        if math.fabs( dist ) < self.radius:
            return True


class Node( object ):

    def __init__( self, label, pos, ins, outs ):
        self.label = label
        #self.pos = pos
        self.pos = wx.Point( pos[0], pos[1] )

        self._idx = wx.NewId()
        self.size = (100, 100)
        self.ins = ins
        self.outs = outs
        self.idx = wx.NewId()
        self.selected = False
        self.drawn = False

        # HAXXOR
        self.plugs = []
        for i, in_ in enumerate( self.ins ):
            plug = Plug( (PLUG_RADIUS, 20 + PLUG_SPACING * i), PLUG_RADIUS, PLUG_TYPE_IN, self )
            self.plugs.append( plug )
        for i, out in enumerate( self.outs ):
            plug = Plug( (self.size[0] - PLUG_RADIUS - 1, 20 + PLUG_SPACING * i), PLUG_RADIUS, PLUG_TYPE_OUT, self )
            self.plugs.append( plug )

        self.wires = []

    def Draw( self, dc ):
        x, y = self.pos
        w, h = self.size
        dc.DrawRoundedRectangle( x, y, w, h, 5 )
        dc.DrawText( self.label, x, y )

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


class NodeGraph( wx.ScrolledWindow ):
    def __init__(self, parent, id, log, size = wx.DefaultSize):
        wx.ScrolledWindow.__init__(self, parent, id, (0, 0), size=size, style=wx.SUNKEN_BORDER)

        self.nodes = {}
        self._startPos = None
        self._pos = None

        self.srcNode = None
        self.srcPlug = None

        self.maxWidth  = W
        self.maxHeight = H
        self.x = self.y = 0

        self.SetBackgroundColour( 'WHITE' )
        self.SetVirtualSize( (self.maxWidth, self.maxHeight) )
        self.SetScrollRate( 20, 20 )
        
        # create a PseudoDC to record our drawing
        self.pdc = wx.PseudoDC()
        self.Bind( wx.EVT_PAINT, self.OnPaint )
        self.Bind( wx.EVT_ERASE_BACKGROUND, lambda x: None )
        self.Bind( wx.EVT_MOUSE_EVENTS, self.OnMouse )
        
        # vars for handling mouse clicks
        self.dragid = -1
        self.lastpos = (0,0)

    def AddNode( self, label, pos, ins, outs ):
        node = Node( label, pos, ins, outs )
        self.nodes[node._idx] = node
        self.DoDrawing( self.pdc )
        return node
    
    def ConvertEventCoords(self, event):
        xView, yView = self.GetViewStart()
        xDelta, yDelta = self.GetScrollPixelsPerUnit()
        return (event.GetX() + (xView * xDelta),
            event.GetY() + (yView * yDelta))

    def OffsetRect(self, r):
        xView, yView = self.GetViewStart()
        xDelta, yDelta = self.GetScrollPixelsPerUnit()
        r.OffsetXY(-(xView*xDelta),-(yView*yDelta))

    def OnMouse(self, event):
        x, y = self.ConvertEventCoords( event )
        winSpacePos = wx.Point( x, y )

        if event.LeftDown():
            #x, y = self.ConvertEventCoords( event )
            
            idxs = self.pdc.FindObjects( x, y, hitradius )
            if idxs:
                self.dragid = idxs[0]
                self.lastpos = (event.GetX(),event.GetY())

            if self.dragid in self.nodes:
                node = self.nodes[self.dragid]
                plug = node.HitTest( winSpacePos )
                if plug is not None:
                    self._startPos = x, y
                    self.srcNode = node
                    self.srcPlug = plug

        elif event.Dragging() or event.LeftUp():
            if self.dragid != -1 and self._startPos is None:
                x,y = self.lastpos
                dx = event.GetX() - x
                dy = event.GetY() - y
                r = self.pdc.GetIdBounds(self.dragid)
                self.pdc.TranslateId(self.dragid, dx, dy)
                r2 = self.pdc.GetIdBounds(self.dragid)
                r = r.Union(r2)
                #r.Inflate(4,4)
                self.OffsetRect(r)
                self.RefreshRect(r, False)
                self.lastpos = (event.GetX(),event.GetY())
                self.nodes[self.dragid].UpdateRect( r )
            if event.LeftUp():
                self.dragid = -1
        
        if event.LeftUp():
            
            # Attempt to make a connection.
            if self.srcPlug is not None:
                for dstNode in self.nodes.values():
                    dstPlug = dstNode.HitTest( winSpacePos )
                    if dstPlug is not None:
                        #pnt1 = (self.srcPlug.pos[0] + self.srcNode.pos[0], self.srcPlug.pos[1] + self.srcNode.pos[1])
                        #pnt2 = (dstPlug.pos[0] + dstNode.pos[0], dstPlug.pos[1] + dstNode.pos[1])
                        #self.DrawWire( pnt1, pnt2, self.pdc)
                        #print 'CONNECT:', self.srcPlug, dstPlug
                        wire = Wire( self.srcNode, self.srcPlug, dstNode, dstPlug )
                        self.srcNode.wires.append( wire )
                        self.DoDrawing( self.pdc )

            self._startPos = self._pos = None
            self.srcPlug = None

        elif event.Dragging():
            self._pos = x, y

            # HAXXOR
            r = wx.Rect( 0, 0, 400, 400 )
            self.RefreshRect(r, True)


    def OnPaint(self, event):
        
        # Create a buffered paint DC.  It will create the real
        # wx.PaintDC and then blit the bitmap to it when dc is
        # deleted.  
        dc = wx.BufferedPaintDC( self )
        # use PrepateDC to set position correctly
        self.PrepareDC( dc )
        # we need to clear the dc BEFORE calling PrepareDC
        bg = wx.Brush( self.GetBackgroundColour() )
        dc.SetBackground( bg )
        dc.Clear()
        # create a clipping rect from our position and size
        # and the Update Region
        xv, yv = self.GetViewStart()
        dx, dy = self.GetScrollPixelsPerUnit()
        x, y = (xv * dx, yv * dy)
        rgn = self.GetUpdateRegion()
        rgn.Offset( x, y )
        r = rgn.GetBox()

        # Draw the temp wire.
        if self._startPos is not None and self._pos is not None:
            self.DrawWire( self._startPos, self._pos, dc )

        # Draw to the dc using the calculated clipping rect.
        self.pdc.DrawToDCClipped( dc, r )

    def DrawWire( self, pos1, pos2, dc ):
        pnts = []
        pnts.append( pos1 )
        pnts.append( (pos1[0] + 20, pos1[1]) )
        pnts.append( (pos2[0] - 20, pos2[1]) )
        pnts.append( pos2 )
        dc.DrawSpline( pnts )

    def DoDrawing( self, dc ):
        print 'Do Drawing'
        #dc.Clear()
        dc.BeginDrawing()
        
        for node in self.nodes.values():
            #if node.drawn:
            #    continue
            dc.SetId( node._idx )
            node.Draw( dc )
            r = wx.Rect( node.pos[0], node.pos[1], node.size[0], node.size[1] )
            dc.SetIdBounds( node._idx, r )
            #node.drawn = True

            # Draw node wires.
            for wire in node.wires:

                dc.SetId( wire._idx )
                wire.Draw( dc )
                pnt1 = wire.node1.pos + wire.plug1.pos
                pnt2 = wire.node2.pos + wire.plug2.pos
                r = wx.Rect( pnt1.x, pnt1.y, pnt2.x - pnt1.x, pnt2.y - pnt1.y )
                dc.SetIdBounds( wire._idx, r )
                #wire.Draw()

        dc.EndDrawing()


class MainFrame( wx.Frame ):

    def __init__( self, *args, **kwargs ):
        wx.Frame.__init__( self, *args, **kwargs )

        pnl = wx.Panel( self, wx.ID_ANY, size=(200,30) )
        ng = NodeGraph( pnl, wx.ID_ANY, None )
        #ng.AddNode( 'foo', (66, 66), [], ['a', 'b', 'c'] )
        #ng.AddNode( 'bar', (200, 10), ['a', 'b', 'c'], [] )
        ng.AddNode( '1', (66, 66), [], ['a'] )
        ng.AddNode( '2', (66, 200), [], ['a'] )
        ng.AddNode( 'Add', (200, 80), ['a', 'b'], [] )
        sz = wx.BoxSizer( wx.VERTICAL )
        sz.Add( ng, 1, wx.EXPAND )
        pnl.SetSizerAndFit( sz )


if __name__ == '__main__':
    app = wx.App( redirect=False )
    top = MainFrame( None, title='foo', pos=(0, 0), size=(700, 600) )
    top.Show()
    app.SetTopWindow( top )
    app.MainLoop()