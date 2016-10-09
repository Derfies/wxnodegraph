import math

import wx

from constants import *
from wire import Wire


class Plug( object ):

    def __init__( self, text, pos, radius, type_, node ):
        self._text = text
        self._node = node
        self._pos = wx.Point( pos[0], pos[1] )  # In node space
        self.radius = radius
        self._type = type_

        self._wires = []

    def GetText( self ):
        return self._text

    def SetText( self, text ):
        self._text = text

    def GetType( self ):
        return self._type

    def SetType( self, type_ ):
        self._type = type_

    def GetNode( self ):
        return self._node

    def SetNode( self, node ):
        self._node = node

    def GetPosition( self ):
        return self._pos

    def SetPosition( self, pos ):
        self._pos = pos

    def GetWires( self ):
        return self._wires

    def Draw( self, dc ):
        final = self._pos + self._node.GetRect().GetPosition()
        dc.SetPen( wx.Pen( 'grey',style=wx.TRANSPARENT ) )
        dc.SetBrush( wx.Brush( 'black', wx.SOLID ) )
        dc.DrawCircle( final.x, final.y, self.radius )

        # HAXXOR
        newFont = wx.SystemSettings_GetFont( wx.SYS_DEFAULT_GUI_FONT )
        tdc = wx.WindowDC( wx.GetApp().GetTopWindow() )
        tdc.SetFont( newFont )
        w, h = tdc.GetTextExtent( self._text )

        dc.SetFont( newFont )
        if self._type == PLUG_TYPE_IN:
            x = final.x + PLUG_TITLE_MARGIN
        else:
            x = final.x - w - PLUG_TITLE_MARGIN

        dc.DrawText( self._text, x, final.y - h / 2 )

    def HitTest( self, pos ):
        pnt = pos - self._pos
        dist = math.sqrt( math.pow( pnt.x, 2 ) + math.pow( pnt.y, 2 ) )
        if math.fabs( dist ) < PLUG_HIT_RADIUS:
            return True

    def CanConnect( self ):
        pass

    def Connect( self, dstPlug ):
        print 'Connecting:', self, '->', dstPlug
        pt1 = self.GetNode().GetRect().GetPosition() + self.GetPosition()
        pt2 = dstPlug.GetNode().GetRect().GetPosition() + dstPlug.GetPosition()
        wire = Wire( pt1, pt2, self.GetType() )
        wire.srcNode = self.GetNode()
        wire.dstNode = dstPlug.GetNode()
        wire.srcPlug = self
        wire.dstPlug = dstPlug
        self._wires.append( wire )
        dstPlug.GetWires().append( wire )

        dc = self.GetNode().GetParent().pdc
        wire.Draw( dc )
        self.GetNode().GetParent().RefreshRect( wire.GetRect(), False )

    def Disconnect( self ):
        '''
        # HAXXOR
        for wire in self._wires:
            print 'del:', wire
            del wire.srcNode# = self.GetNode()
            del wire.dstNode# = dstPlug.GetNode()
            del wire.srcPlug# = self
            del wire.dstPlug# = dstPlug
            self.GetNode().GetParent().RefreshRect( wire.GetRect(), False )
        self._wires = []

            #print 'disconnect:', wire
        '''