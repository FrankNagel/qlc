#!/usr/bin/perl -w

# From a csv of vowel sequences and counts, output each vowel sequence
# with its probability of being a diphthong (as opposed to a syllable
# boundary). Format of the csv is:
#
# vowel_sequence is_diphthong count

$prev = "";
$total = 0;
$yes = 0;

while (<>) {
    local @columns = split;
    @columns == 3 or die "Badly formatted row: $_\n";
    local ($current, $is_diphthong, $count) = @columns;
    if ($current ne $prev) {
	# Hit the next current, so print prob for the previous one.
	$prev ne "" and printProb();
	$prev = $current;
	$total = 0;
	$yes = 0;
    }
    $total += $count;
    if ($is_diphthong eq "yes") {
	$yes += $count;
    } elsif ($is_diphthong ne "no") {
	die "Second column should be \"yes\" or \"no\": $_\n";
    }
}
# Reached the end, so print prob for the last current (which is prev).
printProb();

sub printProb {
    $total > 0 or die "All counts for $prev are 0.\n";
    my $prob = $yes * 1.0 / $total;
    print "$prev\t$prob\n";
}
