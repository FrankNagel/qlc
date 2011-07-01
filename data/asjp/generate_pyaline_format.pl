#!/usr/bin/env perl

# Perl trim function to remove whitespace from the start and end of the string
sub trim($)
{
    my $string = shift;
    $string =~ s/^\s+//;
    $string =~ s/\s+$//;
    return $string;
}

my $fam1 = "";
my $fam2 = "";
my $lang = "";

my $latitude = "";
my $longitude = "";
my $nr_of_speakers = "";
my $wals_code = "";
my $iso_code = "";

my @concepts = (('') x 100);
my $go = 0;
my %files = {};

foreach $line(<>) {
    chomp($line);
    $line =~ s/[\n\r]//g;
    
    if ( ($go == 0) and ($line =~ '^GWI') ) {
        $go = 1;
    }
    next if ($go == 0);
    if ($line =~ /^[A-Z]/) {
        if ($line =~ /(^[^{]+)\{([^|]+)\|([^}]+)\}/) {
            $lang_new = $1;
            $fam1_new = $2;
            $fam2_new = $3;
            # this if statements filters the languages; only languages in family starting with "Sal." in this case
            if ($fam1 =~ /Sal\./) {
                print join("\t", $lang, $fam1, $fam2, $iso_code, $wals_code, $nr_of_speakers, $latitude, $longitude);
                foreach $string(@concepts) {
                    print "\t$string";
                }
                print "\n";
            }
            $lang = $lang_new;
            $fam1 = $fam1_new;
            $fam2 = $fam2_new;
            @concepts = (('') x 100);
        }
    }
    elsif ($line =~ /^\d/) {
        #print $line;
        ($nr_concept, $string) = split(/\t/, $line);
        ($nr, $concept) = split(/ /, $nr_concept);
        $string =~ s/, ?/|/g;
        $string =~ s/\r\n//g;
        $string =~ s/\/\/.*$//;
        $string =~ s/XXX//;
        $string =~ s/ +/ /g;
        $string = "" if $string eq " ";
        $concepts[$nr-1] = $string;
    }
    elsif ($line =~ /^ \d/) {
        $longitude = trim(substr($line, 3, 7));
        $latitude = trim(substr($line, 11, 7));
        $nr_of_speakers = trim(substr($line, 18, 12));
        $wals_code = substr($line, 33, 3);
        $iso_code = substr($line, 39, 3);
    }
    
}
