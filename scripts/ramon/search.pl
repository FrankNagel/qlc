#!/usr/bin/perl -w

use strict;

print "Bitte Dateiname eingeben: ";
chop(my $filename=<STDIN>);

open(FH, "<$filename")
         or
         die "Konnte $filename nicht öffnen\n";

#undef $/;

while(my $search=<FH>){
    chomp ($search);
            if($search=~m/^[a-z]/gi) {
                   print "$search gefunden\n";
                  }
      }
close FH
