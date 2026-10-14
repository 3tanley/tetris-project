"""Jaws (ILSZ) 1st PC from https://four.lol/perfect-clears/ILSZ ("A 100% 1st PC pattern").

The opener is just 4 pieces: I L S Z on the left (rows top -> bottom). Every solution is
a 4-line PC on top of it with the other 6 pieces (the rest of bag 1 + some of bag 2),
which leaves 4 pieces of bag 2 for the 2nd PC (setups_fourlol_2pc.py).
  ILSZ    22 minimal solutions (together they cover every piece order: 100%)
  ILOSZ   an O on the far right: 33 solutions (92.26%; 100% if the O is one of the first
          3 pieces of bag 2)
  ILJOSZ  J and O placed like FIELD_ILJOSZ: 15 solutions (58.33%). four.lol draws these
          after the full row clears; templates.py puts the row back.
four.lol's "Solution Search for ILSZ" (all 605 solutions by piece order) is a server
query (api.four.lol); the bot does the same check itself for every solution here
against the queue + hold. Fumens copied from the page data; mirrors are made in code.
"""

BUILD = [
    "I L L L . . . . . .",
    "I L Z . . . . . . .",
    "I Z Z S S . . . . .",
    "I Z S S . . . . . .",
]
FIELD_ILOSZ = "v115@9gwhilFewhglAtGewhBtR4CeRpwhAtR4DeRpJeAgH"
FIELD_ILJOSZ = "v115@9gwhilFewhglAtGewhBtR4i0RpwhAtR4Ceg0RpJeAg?H"

SOLUTIONS_ILSZ = "v115@9gD8R4hlRpC8R4g0wwglRpE8g0xwRpD8h0wwglRpJe?Ag0GAv/VWCPNBAADhxhRpFegWwhQpglFehWhlFegWwhQpgl?JeAg0GA0vaPCPNBAABhhHhWxSCehWQaxhwSgWEewSAeQpxh?DeQawSAewhgWwhJeAg0GAvfjxCP+AAABhCtwwRpCeRaAewh?glRpEehlAexSDeQawhhlQawSJeAg0GAv/lFDqOBAABhCPQL?GehWBeQaEehWAehlFewhAeQpglJeAg0GAq+aFDK+AAABhCt?whBPEehlAPwSgWEehlAehWFeQaBewhJeAg0GAKHmFDsOBAA?ChxhAtxhCexhAewSAtGexhGehWwSAexSJeAg0GAvvKxCs/A?AABhAPSLRaCeRagWwhAeglQaEexSAehlDehlAtAeglQaJeA?g0GAq+aFDM+AAABhh0BeRaCeSpglAPwSFeQpglQahWDehlQ?aAPgWwhJeAg0GAv/VWCT+AAABhhHBexwCehWQagWwhAtQpF?ehWhlDeQaAewhAtQpglJeAg0GAKHmPCU+AAABhh0BeRLCeh?lAehlwSgWEeQaglQphWEeRaBewhJeAg0GAq+ytCU+AAABhh?HBexhCehWAehWglQaEewhgWwShlEexhAeQaAPJeAg0GAKHW?WCU+AAABhAtwwBeRaEewhRpglwwEewSAeQpxhEexSwhglAt?JeAg0GAvvTxCK+AAAChQaAtywCeSaBPQLQaEeRpAexSDeQa?whRaAPwSJeAg0GAvfjWCqOBAABhyhCPCexhAeAtAewwwhEe?xSAeRpDewhQaxhAtQpJeAg0GAvvTxCs/AAABhQaBPAeBtEe?xSwhQagWEeQpAewSRaEeRpSaJeAg0GAKHmPC0CBAABhglww?hlxSCehlQphlwSgWEeQaglQpxhEeRahWwhJeAg0GA0vytC0?XBAABhgWAeQpFehWAeRaGexhAexSDehlQaglQawSJeAg0GA?vfrgCUNBAAChhWaehWNeAg0GAvfjxCvOBAAChhWglRpEeAP?xSgWQpOegWQaMeAg0GAv/NMCKHBAAChRpQLxSEewwAtAegl?wSEeRaQLGeQpglQLLeAg0GAve9wCKHBAAChxhAthlEeQaAP?AehWEeRawwRpDeglwhQaQpglQpJeAg0GAqubMCzOBAA"
SOLUTIONS_ILOSZ = "v115@9gD8R4hlRpC8R4g0wwglRpE8g0xwF8h0wwglB8JeAg?0FAqOMgCzAAAADhBtHewhQpRewhQpLeAg0FAquHgCzAAAAB?hhHRLEehWQawhglHexhFeQayhLeAg0FAKNegCpAAAAKhRaw?hRaGeSaFeQawSgWMeAg0FA03HgCpAAAABhh0BehWCeRpAeQ?aAPRaEewhHehlAeAPLeAg0FAqOstCpAAAABhhWAtywCexSQ?aAeCtEeQaAewhFehWAeAtLeAg0FAquzPC0AAAAChxhAexSC?exhAewSAexSEexhGehWwSMeAg0FAKHWWCqAAAAChSLgWQaE?egWwhAPRaNeQpxhMeAg0FAq+KWCpAAAAChCtglwhEehlAtx?hEexhGeglAtQpMeAg0FAK9KxC0AAAABhhlAewhRpCehlCeR?pEehWGehWQaMeAg0FA0/9tCqAAAABhgWQLwSFehWAewSIew?SWeAg0FA0/VWCqAAAAChRpFeRaBeBPFewhAtGeRawSMeAg0?FAqXUPC0AAAABhhlAeRaAPCeRpwhQpBeAPFeRaFehlQpQaL?eAg0FAqOstC0AAAABhhWAeQagWwhCehWRaglxhFexhFeSaw?hLeAg0FAqXegC0AAAAChhWglRpEeAPxSgWQpOegWQaMeAg0?FAqeNPCvAAAABhwhhlQaxSCexhwwBtglwSFeRaFewhRpQaL?eAg0FAq+KxCqAAAABhQaHeRaAPxSHexhFeQaAPQawhLeAg0?FAqOMgC0AAAABhhWBeglQaCexhAtQpAeRaFeRaFegWwhAeQ?aLeAg0FA0iHgC0AAAABhglQawSxhAtCeSawSCtEewhglwhF?eBtwSwhLeAg0FAKNWWCqAAAAChhlIeQpRaHeQaHeglgWLeA?g0FA0untC6AAAAChRpRexSWeAg0FA0uPFDzAAAAChRLAPxS?EewSQawhgWwSGewhFegWwShlLeAg0FAqXegCsAAAAChRpAt?RpCeBPQawSAeRpEewhgWGewSgWAPMeAg0FAqSNPC0AAAACh?xhCPCeBtwwAeSLFeQpQaFeQpAtQpAPLeAg0FA0u3LCsAAAA?BhwhBeCtEeQawwh0wwEeySGeAPglwwLeAg0FAqyTxCqAAAA?BhxhQaQLxSCehlAeQagHAPwSEeRpQaGeQpgWgHLeAg0FAUu?KxCzAAAABhRawhwwQpQaCehHBPwhRaFewhwwIewwLeAg0FA?0SNPCqAAAABhQahWBeAtCeBtBeRaAtEewSBPGewSQagWLeA?g0FAqCOMC6AAAAChglwhCPEeAtCeQLEeAtRpFewhAtwhgWL?eAg0FAUe/wCsAAAAChwSgWCtFeCtwwEewSgWGeRLAPQaLeA?g0FAU+lPCvAAAAChBtCPFeCPQLEexhwSFeh0RpLeAg0FA0n?9VCzAAAAChhWFeRaJexhQpFexSwhgWLeAg0FA0n9wCsAAAA?BhwhRaFehlwhIewhRaFehlwhMeAg0FAKezPCsAAAA"
SOLUTIONS_ILJOSZ = "v115@HhD8zhRpC8BtywRpD8BtwwC8JeAg0EAaHOMCUhxhAe?hlFewhQpglMeAAtEATHOMCLhAtywHeQLQaFewSRLMeAAtEA?vOUPCMhSLgWQaEegWwhAPRaDeQpxhMeAAtEAs+CMCMhxwQp?glwhEeQpwhglxhEeQpwhMeAAtEAvXmPCMhBPgWGeAPRpGew?hQpMeAAtEATHWWCMhRpAtRpCeRaQpRLQaQpDeQawSQLMeAA?tEA6i/wCMhhlgWxSCexhAehlwhwSDeRpglMeAAtEAvX+tCM?hRLgWHexhFegWQLwhMeAAtEAvOWWCMhRpglHeRaGeQpQaMe?AAtEAvXWxCMhhWglRpEeAPxSgWQpEegWQaMeAAtEAUeHgCM?hQpAtwhxSEeywglwSEeBtMeAAtEAvuntCMhwhAeQaRpEeQa?BPQaQpDeglAeQLMeAAtEAsuntCMhhWQehWNeAAtEAsu/wCL?hhlwSFehlAPSaEexSNeAAtEATe/VC"
