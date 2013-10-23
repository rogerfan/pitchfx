#! /usr/bin/perl

# This script is made freely available for non-commerical use by Mike Fast
# February 2008
# http://fastballs.wordpress.com/
# Attribution is appreciated but not required.

# MySQL database connection statement
use DBI;
$dbh = DBI->connect("DBI:mysql:database=pitch f/x;host=localhost", 'root', '') 
or die $DBI::errstr;

# Get all pitch info from database
$all_pitches_query = "SELECT pitch_id, ab_id, des, type FROM pitches WHERE ball IS NULL ORDER BY pitch_id ASC";
#$all_pitches_query = "SELECT pitch_id, ab_id, des, type FROM pitches ORDER BY pitch_id, ab_id ASC ";
$sth= $dbh->prepare($all_pitches_query) or die $DBI::errstr;
$sth->execute();

# Process each pitch and store result in an array
$old_ab_id = 0;
$ball = 0;
$strike = 0;
while ($hash_ref = $sth->fetchrow_hashref)  {
    $pitch=$hash_ref->{pitch_id};
    $ab=$hash_ref->{ab_id};
    $des=$hash_ref->{des};
    $type=$hash_ref->{type};
    # Store count from previous pitch into ball/strike hashes for this pitch
    if ($ab > $old_ab_id || $old_ab_id==0) 
    {
      $ball = 0;
      $strike = 0;
      print "$ab: $pitch: $des: $ball: $strike:\n";
      $update_count_query = "UPDATE pitches SET ball=$ball, strike=$strike WHERE pitch_id = $pitch";
      $sth2= $dbh->prepare($update_count_query) or die $DBI::errstr;
      $sth2->execute();
      # Process ball, strike, or foul (no strike) for new pitch
      if ("B" eq $type)
      {
        $ball++;
      }
      if ("S" eq $type)
      {
        # Do not count a strike if a pitch is fouled off with two strikes in the count
        if (2 == $strike && ("Foul" eq $des || "Foul (Runner Going)" eq $des))
        {
            # don't increment
        }
        else
        {
          $strike++;
        }
      }
    } 
    elsif($ab == $old_ab_id)  
    {
      print "$ab: $pitch: $des: $ball: $strike:\n";
      $update_count_query = "UPDATE pitches SET ball=$ball, strike=$strike WHERE pitch_id = $pitch";
      $sth2= $dbh->prepare($update_count_query) or die $DBI::errstr;
      $sth2->execute();
      # Process ball, strike, or foul (no strike) for new pitch
      if ("B" eq $type)
      {
        $ball++;
      }
      if ("S" eq $type)
      {
        # Do not count a strike if a pitch is fouled off with two strikes in the count
        if (2 == $strike && ("Foul" eq $des || "Foul (Runner Going)" eq $des))
        {
            # don't increment
        }
        else
        {
          $strike++;
        }
      }
    }
    $old_ab_id = $ab;
}
$sth->finish();
#    $lock_table = 'lock table pitches WRITE';
#    $sth2= $dbh->prepare($lock_table) or die $DBI::errstr;
#    $sth2->execute();

#print "\nFinished accounting for balls and strikes.  Beginning database update...\n";

#for my $pitch_id (keys %store_ball) {
#    my $update_ball = $store_ball{$pitch_id};
#    my $update_strike = $store_strike{$pitch_id};
#    print "$pitch_id: $update_ball-$update_strike.\n";
#    $update_count_query = "UPDATE pitches SET ball=$update_ball, strike=$update_strike WHERE pitch_id = $pitch_id";
#    $sth= $dbh->prepare($update_count_query) or die $DBI::errstr;
#    $sth->execute();
#}
   
#    $unlock_table = 'unlock tables';
#    $sth1= $dbh->prepare($unlock_table) or die $DBI::errstr;
#    $sth1->execute();

