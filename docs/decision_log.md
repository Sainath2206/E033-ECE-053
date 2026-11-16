# ECE-053 -- EMC/EMI Test Lab Job Quoting and Scheduling Engine

## Decision Log

**Team:** E033\
**Project ID:** ECE-053\
**Team members:** Sainath C S and Sanjeev K T

This log records the main design and implementation decisions for the
project. It is based on the project structure and business rules shared
so far. Check each item against the final source code before submission.

  ----------------------------------------------------------------------------
  ID                Area              Decision              Rationale / effect
  ----------------- ----------------- --------------------- ------------------
  DL-01             Programming       Use Python for the    Python supports
                    language          application.          command-driven
                                                            processing,
                                                            calculation logic,
                                                            CSV handling and
                                                            automated tests.

  DL-02             Application       Use a                 Commands can be
                    interface         command-file-driven   supplied
                                      workflow rather than  consistently and
                                      a graphical           processed
                                      interface.            repeatably.

  DL-03             Input and output  Use CSV files for     CSV files are
                    format            chamber, test         straightforward to
                                      catalogue, holiday    inspect and suit
                                      and generated result  the tabular
                                      data.                 project data.

  DL-04             Code organisation Separate the          Separating
                                      application entry     responsibilities
                                      point, processing     makes the code
                                      logic and engine      easier to
                                      logic across          understand, test
                                      `main.py`,            and maintain.
                                      `processor.py` and    
                                      `engine.py`.          

  DL-05             Automated         Keep automated checks A dedicated test
                    verification      in `tests.py`.        suite checks
                                                            business-rule
                                                            behaviour
                                                            independently of a
                                                            normal application
                                                            run.

  DL-06             EUT pricing       Apply factor 1.0 for  This follows the
                    factor            one EUT, 1.5 for two  project
                                      or three EUTs, and    business-rule
                                      2.0 for four or more  quantity bands.
                                      EUTs.                 

  DL-07             Test duration     Multiply base hours   This follows the
                                      by the EUT factor,    specified duration
                                      then round up to the  calculation and
                                      next 0.5 hour.        uses half-hour
                                                            increments.

  DL-08             Test and report   Calculate test cost   This keeps chamber
                    charges           from test hours and   usage charges and
                                      the chamber hourly    the per-job report
                                      rate; add the         fee distinct.
                                      specified ₹8,000      
                                      report fee per job.   

  DL-09             Bundle discount   Apply 5% to gross     This follows the
                                      test costs for 3--4   bundle thresholds
                                      tests and 10% for 5   and excludes the
                                      or more tests. Do not report fee from
                                      discount the report   the discount.
                                      fee.                  

  DL-10             Rush handling     Apply a 40% surcharge Rush pricing
                                      to gross test costs   depends on the
                                      only if the complete  scheduling
                                      job can be scheduled  outcome, not just
                                      within the first five the request flag.
                                      working days after    
                                      confirmation.         
                                      Otherwise downgrade   
                                      to normal pricing and 
                                      remove the surcharge. 

  DL-11             Chamber           Start booking on the  This gives
                    scheduling        first working day     deterministic
                                      after confirmation.   scheduling while
                                      Process tests in      respecting chamber
                                      catalogue order;      compatibility and
                                      choose the earliest   capacity.
                                      working day with a    
                                      matching chamber,     
                                      considering chamber   
                                      IDs in order. Do not  
                                      split a test across   
                                      chamber slots.        

  DL-12             Setup time        Add one hour for the  This accounts for
                                      first test of a job   initial setup
                                      on a chamber on a     without repeatedly
                                      given day. Do not add adding it within
                                      setup again for later the same
                                      tests from the same   job/chamber/day.
                                      job on that chamber   
                                      and day.              

  DL-13             Working days      Exclude weekends and  This avoids
                                      dates listed in the   bookings on
                                      holiday data when     non-working days
                                      scheduling.           and uses the
                                                            supplied holiday
                                                            information.

  DL-14             Quote validity    Accept confirmation   This applies the
                                      through the 30th      30-calendar-day
                                      calendar day after    validity window,
                                      the quote date;       inclusive of day
                                      reject confirmation   30.
                                      after that period.    

  DL-15             Retest pricing    Price a qualifying    This implements
                                      retest at 50% of test the retest time
                                      cost when it is       window and
                                      within 30 days        distinguishes
                                      inclusive of the      eligible retests
                                      failed test's booked  from normal tests.
                                      day. Do not add the   
                                      report fee for that   
                                      retest. Otherwise use 
                                      normal pricing.       

  DL-16             Tax and money     Apply 18% GST to the  This ensures
                    precision         subtotal and use      consistent tax
                                      half-up rounding to   calculation and
                                      two decimal places    currency
                                      for monetary values.  precision.

  DL-17             Error handling    Generate separate CSV Separate outputs
                    and outputs       outputs for           make summaries,
                                      quotations, quote     line-level
                                      lines, chamber        details,
                                      calendar and errors.  scheduling results
                                                            and rejected
                                                            commands easier to
                                                            inspect.
  ----------------------------------------------------------------------------

## Notes on interpretation

-   The decisions above are recorded from the project specification and
    project details shared so far.
-   Check the final source code to ensure each decision matches the
    implementation.
-   This log records decisions and rationale; it does not replace source
    code, test results or the design document.

## Final review checklist

-   [ ] Confirm each decision matches the final implementation.
-   [ ] Confirm the README run instructions match the current project.
-   [ ] Run the complete test suite and record the actual result.
-   [ ] Commit this file to `docs/decision_log.md`.
