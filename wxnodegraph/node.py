import wx

from plug import Plug
from constants import *


class Node( object ):
    
    def __init__( self, parent, text='', colour='white', data=None, rect=wx.ID_ANY, id=wx.ID_ANY, ins=None, outs=None ):
        self._parent = parent
        self._text = text
        self._colour = colour
        self._data = data
        self._rect = rect#wx.Rect()
        self._plugs = []

        if id == wx.ID_ANY:
            self._id = wx.NewId()
        else:
            self._id = id

         # HAXXOR
        x, y, w, h = self._rect.Get()
        for i, plugName in enumerate( ins + outs ):
            plugType = PLUG_TYPE_IN
            x = PLUG_MARGIN
            if plugName in outs:
                x = w - x
                plugType = PLUG_TYPE_OUT
            plug = Plug( plugName, (x, 40 + PLUG_SPACING * i), PLUG_RADIUS, plugType, self )
            self._plugs.append( plug )
    
    def GetId( self ):
        return self._id

    def SetId( self, id_ ):
        self._id = id_

    def GetType( self ):
        return self._type

    def SetType( self, type_ ):
        self._type = type_

    def GetText( self ):
        return self._text

    def SetText( self, text ):
        self._text = text

    def GetData( self ):
        return self._data 
        
    def SetData( self, data ):
        self._data = data 

    def GetRect( self ):
        return self._rect

    def SetRect( self, rect ):
        self._rect = rect
  
    def GetColour( self ):
        return self._colour

    def SetColour( self, colour ):
        self._colour = colour

    def IsSelected( self ):
        pass

    def Enable( self, enable=True ):
        self._enabled = enable

    def IsEnabled( self ):
        return self._enabled

    def GetPlugs( self ):
        return self._plugs

    def FindPlug( self, plugName ):
        for plug in self._plugs:
            if plug.GetText() == plugName:
                return plug

    def GetParent( self ):
        return self._parent

    def HitTest( self, x, y ):
        for plug in self._plugs:
            if plug.HitTest( wx.Point( x, y ) - self._rect.GetPosition() ):
                return plug

    def Draw( self, dc ):
        x, y, w, h = self._rect.Get()

        dc.SetId( self._id )

        dc.SetPen( wx.Pen( 'black', 1 ) )
        dc.SetBrush( wx.Brush( self._colour, wx.SOLID ) )
        dc.DrawRoundedRectangle( x, y, w, h, ROUND_CORNER_RADIUS )

        newFont = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        newFont.SetWeight( wx.BOLD )
        dc.SetFont( newFont )

        dc.DrawText( self._text, x + TITLE_INSET_X, y + TITLE_INSET_Y )

        # Draw ins / outs.
        for plug in self._plugs:
            plug.Draw( dc )

        dc.SetIdBounds( self._id, self._rect )