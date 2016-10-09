import wx

from constants import *


class Wire( object ):
    
    def __init__( self, pnt1, pnt2, dir_ ):
        self.pnt1 = pnt1
        self.pnt2 = pnt2
        self._id = wx.NewId()
        self.dir = dir_

        # HAXXOR
        self.pen = wx.Pen( WIRE_COLOUR, WIRE_THICKNESS )

    def GetId( self ):
        return self._id

    def SetId( self, id_ ):
        self._id = id_

    def Draw( self, dc ):
        dc.SetId( self._id )

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
        
        dc.SetIdBounds( self._id, self.GetRect() )

    def GetRect( self ):
        minX = min( self.pnt1[0], self.pnt2[0] )
        minY = min( self.pnt1[1], self.pnt2[1] )
        size = self.pnt2 - self.pnt1
        rect = wx.Rect( minX - 10, minY, abs( size[0] ) + 20, abs( size[1] ) )
        return rect.Inflate( self.pen.GetWidth(), self.pen.GetWidth() )