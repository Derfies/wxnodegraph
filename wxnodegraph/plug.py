import math

import wx

from constants import *


class Plug( object ):

    def __init__( self, pos, radius, type_, node ):
        self.pos = wx.Point( pos[0], pos[1] )  # In node space
        self.radius = radius
        self.type = type_
        self.node = node

        self.wires = []

    def Draw( self, dc ):
        final = self.pos + self.node.GetRect().GetPosition()
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