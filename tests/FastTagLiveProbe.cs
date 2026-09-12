// Manual live UI probe; compile against the rebuilt TagManager and bundled WPF DLLs.
// Load once in Max and invoke individual methods via MAXScript. Never changes the scene.
using System;
using System.Linq;
using System.Reflection;
using System.IO;
using System.Web.Script.Serialization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using TagManager;

public static class FastTagLiveProbe
{
    static object Field(object owner, string name)
    {
        return owner.GetType().GetField(name, BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic).GetValue(owner);
    }
    static FastWPFTag Fast { get { return TagGlobals.tagCenter.fastTag; } }
    static dragonz.actb.control.AutoCompleteTextBox Box { get { return (dragonz.actb.control.AutoCompleteTextBox)Field(Fast, "actbFastBox"); } }
    public static string State()
    {
        var manager = Box.AutoCompleteManager;
        var popup = (Popup)Field(manager, "_popup");
        var list = (ListBox)Field(manager, "_listBox");
        return new JavaScriptSerializer().Serialize(new {
            text = Box.Text, open = popup.IsOpen, paths = list.Items.Cast<object>().Select(Convert.ToString).ToArray(),
            selected = list.SelectedIndex, height = Fast.winParent.Height, loaded = Fast.IsLoaded
        });
    }
    public static string Key(string key)
    {
        var args = new KeyEventArgs(Keyboard.PrimaryDevice, PresentationSource.FromVisual(Box), Environment.TickCount,
            (Key)Enum.Parse(typeof(Key), key)) { RoutedEvent = Keyboard.PreviewKeyDownEvent };
        Box.RaiseEvent(args);
        return "handled=" + args.Handled;
    }
    public static void Text(string value) { Box.Text = value; }
    public static void Close() { Fast.winParent.Close(); }
    public static string Capture(string path)
    {
        var popup = (Popup)Field(Box.AutoCompleteManager, "_popup");
        var child = (FrameworkElement)popup.Child;
        var bitmap = new RenderTargetBitmap((int)Math.Ceiling(child.ActualWidth), (int)Math.Ceiling(child.ActualHeight), 96, 96, PixelFormats.Pbgra32);
        bitmap.Render(child);
        var png = new PngBitmapEncoder(); png.Frames.Add(BitmapFrame.Create(bitmap));
        using (var stream = File.Create(path)) png.Save(stream);
        return path;
    }
    public static string Shapes()
    {
        var dimensions = new[] { new[] { 10d, 8d, .2 }, new[] { 5d, .2, 3d }, new[] { .3, .3, 4d }, new[] { 6d, .3, .4 }, new[] { 20d, 15d, 10d }, new[] { 1d, 1d, 1d } };
        string[] expected = { "Slabs", "Walls", "Columns", "Beams", "Volumes", "Cabinets" };
        for (int i = 0; i < dimensions.Length; i++) {
            var d = dimensions[i]; var guesses = ArchitecturalSuggestions.FromDimensions(d[0], d[1], d[2]);
            if (!guesses[0].Path.EndsWith(expected[i])) throw new Exception("Wrong shape prior " + expected[i]);
            if (guesses.Any(g => g.Score < 0 || g.Score > 1)) throw new Exception("Invalid score");
        }
        if (ArchitecturalSuggestions.FromDimensions(double.NaN, 1, 1).Count != 0 || ArchitecturalSuggestions.FromDimensions(0, 0, 0).Count != 0) throw new Exception("Invalid dimensions accepted");
        return "PASS: six architectural shapes and invalid/zero extents";
    }
}
