import math

import wx

from constants import *


class Plug( object ):

    def __init__( self, text, pos, radius, type_, node ):
        self._text = text
        self.pos = wx.Point( pos[0], pos[1] )  # In node space
        self.radius = radius
        self.type = type_
        self.node = node

        self._wires = []

        #self._connectedPlug

    def GetText( self ):
        return self._text

    def SetText( self, text ):
        self._text = text

    def GetWires( self ):
        return self._wires

    def Draw( self, dc ):
        final = self.pos + self.node.GetRect().GetPosition()
        dc.SetPen( wx.Pen( 'grey',style=wx.TRANSPARENT ) )
        dc.SetBrush( wx.Brush( 'black', wx.SOLID ) )
        dc.DrawCircle( final.x, final.y, self.radius )

        # HAXXOR
        newFont = wx.SystemSettings_GetFont( wx.SYS_DEFAULT_GUI_FONT )
        tdc = wx.WindowDC( wx.GetApp().GetTopWindow() )
        tdc.SetFont( newFont )
        w, h = tdc.GetTextExtent( self._text )

        dc.SetFont( newFont )
        if self.type == PLUG_TYPE_IN:
            x = final.x + PLUG_TITLE_MARGIN
        else:
            x = final.x - w - PLUG_TITLE_MARGIN

        dc.DrawText( self._text, x, final.y - h / 2 )

    def HitTest( self, pos ):
        pnt = pos - self.pos
        dist = math.sqrt( math.pow( pnt.x, 2 ) + math.pow( pnt.y, 2 ) )
        if math.fabs( dist ) < PLUG_HIT_RADIUS:
            return True

    def CanConnect( self ):
        pass

    def Connect( self, dstPlug ):
        print 'Connecting:', self, '->', dstPlug
        # wire = Wire( srcNode.GetRect().GetPosition() + srcPlug.pos, dstNode.GetRect().GetPosition() + dstPlug.pos, srcPlug.type )
        #self._connectedPlug = dstPlug

    def Disconnect( self ):
        pass