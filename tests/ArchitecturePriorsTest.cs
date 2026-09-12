// Standalone regression: compile together with TagManager/ArchitecturalSuggestions.cs.
using System;
using System.Diagnostics;
using System.Linq;
using TagManager;

class ArchitecturePriorsTest
{
    static void Main()
    {
        var cases = new[] { new[] { 10d, 8d, .2 }, new[] { 5d, .2, 3d }, new[] { .3, .3, 4d }, new[] { 6d, .3, .4 }, new[] { 20d, 15d, 10d }, new[] { 1d, 1d, 1d } };
        string[] expected = { "Slabs", "Walls", "Columns", "Beams", "Volumes", "Cabinets" };
        for (int i = 0; i < cases.Length; i++) {
            var d = cases[i]; var guesses = ArchitecturalSuggestions.FromDimensions(d[0], d[1], d[2]);
            if (!guesses[0].Path.EndsWith(expected[i])) throw new Exception("Wrong shape prior " + expected[i]);
            if (guesses.Count < 3 || guesses.Any(g => g.Score < 0 || g.Score > 1 || string.IsNullOrEmpty(g.Reason))) throw new Exception("Invalid alternatives");
            var swapped = ArchitecturalSuggestions.FromDimensions(d[1], d[0], d[2]);
            if (!guesses.Select(g => g.Path).SequenceEqual(swapped.Select(g => g.Path))) throw new Exception("XY axis dependence");
        }
        foreach (double bad in new[] { double.NaN, double.PositiveInfinity, -1d })
            if (ArchitecturalSuggestions.FromDimensions(bad, 1, 1).Count != 0) throw new Exception("Invalid dimensions accepted");
        if (ArchitecturalSuggestions.FromDimensions(0, 0, 0).Count != 0) throw new Exception("Zero extent accepted");
        var timer = Stopwatch.StartNew();
        for (int i = 0; i < 100000; i++) ArchitecturalSuggestions.FromDimensions(10, 8, .2);
        Console.WriteLine("PASS: six shape families, XY invariance, invalid/zero extents. 100,000 classifications: " + timer.ElapsedMilliseconds + " ms (priors only, no Max bounds queries).");
    }
}
