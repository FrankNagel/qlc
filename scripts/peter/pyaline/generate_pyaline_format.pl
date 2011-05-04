
my $fam1 = "";
my $fam2 = "";
my $lang = "";

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
    #print $line;
    if ($line =~ /^[A-Z]/) {
        if ($line =~ /(^[^{]+)\{([^|]+)\|([^}]+)\}/) {
            $lang_new = $1;
            $fam1_new = $2;
            $fam2_new = $3;
            if ($fam1 =~ /Sal\./) {
                #print STDERR $lang."\n";
                print "$lang\t$fam1\t$fam2";
                foreach $string(@concepts) {
                    print "\t$string";
                }
                print "\n";
                #if (exists($files{$fam1})) {
                #    $files{$fam1} .= $text;
                #} else {
                #    $files{$fam1} = $text;
                #}
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
        $string =~ s/\\\\.*$//;
        $string =~ s/XXX//;
        $string =~ s/ +/ /g;
        $string = "" if $string eq " ";
        $concepts[$nr-1] = $string;
    }
    
}

#foreach $file(keys(%files)) {
#    open(F, ">$file.csv");
#    print F $files{$file};
#    close(F);
#}