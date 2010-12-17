#!/usr/bin/env perl

#open(DICTATA, "<dictdata.csv");
#my $dictdata = <DICTDATA>;
#close(DICTDATA);

open(ENTRIES, "<entry.csv");
my @entry = <ENTRIES>;
close(ENTRIES);

open(ANNOTATIONS, "<annotation.csv");
my @annotation = <ANNOTATIONS>;
close(ANNOTATIONS);

# hashes for ad-hoc data
my %entry = {};
my %headannotation = {};
my %transannotation = {};

foreach (@entry) {
    chomp;
    my @tmp = split(/\t/);
    my $id = shift(@tmp);
    @{$entry{$id}} = @tmp;
}

foreach (@annotation) {
    chomp;
    my @tmp = split(/\t/);
    if ($tmp[5] eq "head") {
        if (exists($headannotation{$tmp[1]})) {
            push(@{$headannotation{$tmp[1]}}, $tmp[6]);
        } else {
            @{$headannotation{$tmp[1]}} = ($tmp[6]);
        }
    }
    if ($tmp[5] eq "translation") {
        if (exists($transannotation{$tmp[1]})) {
            push(@{$transannotation{$tmp[1]}}, $tmp[6]);
        } else {
            @{$transannotation{$tmp[1]}} = ($tmp[6]);
        }
    }
}

foreach (keys(%entry)) {
    foreach $h(@{$headannotation{$_}}) {
        foreach $t(@{$transannotation{$_}}) {
            print "$h\t$t\n";
        }
    }
}