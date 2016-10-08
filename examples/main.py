import sys
sys.path.append( '../wxnodegraph' )

import wx

import wxnodegraph as wxng


class MainFrame( wx.Frame ):

    def __init__( self, *args, **kwargs ):
        wx.Frame.__init__( self, *args, **kwargs )

        pnl = wx.Panel( self, wx.ID_ANY, size=(200,30) )
        ng = wxng.NodeGraph( pnl, wx.ID_ANY, None )
        sz = wx.BoxSizer( wx.VERTICAL )
        sz.Add( ng, 1, wx.EXPAND )
        pnl.SetSizerAndFit( sz )
        ng.Load( 'math.json' )


if __name__ == '__main__':
    app = wx.App( redirect=False )
    top = MainFrame( None, title='foo', pos=(0, 0), size=(800, 700) )
    top.Show()
    app.SetTopWindow( top )
    app.MainLoop()