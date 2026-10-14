"""DPC (TSD -> PC after an 8-line PC) from https://four.lol/perfect-clears/dpc

Each entry: (name, label, leftover piece, criteria, setup fumen, [PC solution fumens]).
* Page 1 of the setup fumen is the build: grey cells are the piece left over from the
  previous bag, coloured cells are the next bag minus its T (used for the TSD).
  Some pages stack several builds separated by blank rows.
* criteria: "A<B" = A must come before B among the next bag's pieces (from the
  section titles / notes on four.lol, e.g. "JO" = J before O).
* Solution fumens: every page is one 4-line PC solution (grey = what is left after the TSD).
Order = four.lol order (most reliable first). Mirrors (S<->Z, L<->J) are generated in code.
"""

DPC_SETUPS = [
    ('jo-100', 'JO', 'O', 'J<O',
     'v115@0gAtHeBtGewhAtCehlRpg0whB8AeR4glRpg0whB8R4?AeglAeh0whJeAgWKAPq78AQPUABDHBAAIhywHewwaeAAAIh?AtHeBtGeQ4BexhAeg0AehlQ4JeAAPOAPqDfETYk2ARYcRAy?fAAA',
     ['v115@9gilywzhglA8RpwwAth0R4B8RpBtg0R4E8AtA8g0C8?JeAg0HAzfrgCpOkBAAhCPAeh0QpDewhglxhxSDeglwhQagW?wSEeglAeQaMeAg0HAq+aFDT+jBAAhh0QpwwQaAPQaBeBthW?QagWRaBehWQLAPBewhEegWAewhMeAg0HAUePFDPNkBA', 'v115@9gilAtRpzhglA8BtRph0R4B8Atywg0R4E8wwA8g0C8?JeAgWaA2FIOBFbcRAyv78Aw3CwBFbssCq+aFDpCBAA9gilA?tRpwhg0R4glA8BtRpwhi0B8AtywwhR4E8wwA8whC8JeAAPa?AUBIOBFbcRAyv78Aw3CwBFb8KC0vaFDMNBAA']),
    ('oj-100', 'OJ', 'O', 'O<J',
     'v115@1gAtGewhBtGewhAtCehli0whB8AeR4glRpg0whB8R4?AeglRpKeAgWKAvr78AwWUABj/AAAJhywHewwZeAAAJhAtGe?Q4BtGeQ4BexhAeg0xwKeAAPOAvrDfETYk2ARYcRAyfAAA',
     ['v115@9gRphlywAtg0whRpA8glQ4wwBtg0whC8glR4Ath0wh?E8Q4C8whJeAg0HAJtPFDvC2BABhRawhglGeQaAewhHewhRa?UeAg0HAp+jFDvifBA', 'v115@9gRpBtywR4whRpA8BtwwR4glwhC8i0ilwhE8g0C8wh?JeAg0HApintCvX2BA']),
    ('other-100', 'Other', 'O', '',
     'v115@BgRpBeR4AtCeRpAeR4BtBeg0B8ilAtCeg0B8glzhAe?h0TeRpBeilCeRpAeAtglR4Beg0B8BtR4Ceg0B8AtzhAeh0J?eAgHBgxSBexDAPCexSAexDBPBegHBAiWAPCegHBAgWTaAeh?HteywHewwLeAAARhxwBei0CexwAeAtg0xhBeglJeAAA',
     ['v115@9gRpwhh0R4ywRpwhg0R4hlwwAtB8whg0C8glBtB8wh?D8glAtA8JeAg0HA6SltCKH2BAEhySFeRpIeQpVeAAe']),
    ('ol-100', 'OL', 'I', 'O<L',
     'v115@zgglIeglBeAtEewhhlBtR4Beg0whRpAtR4Ceg0whRp?D8Aeh0whJeAgWKAJq78AwWUABjCBAAWhywHewwMeAAAHhg0?Ieg0BeAtEeQ4h0BtxhBeglQ4JeAAPOAJqDfETYk2ARYcRAy?fAAA',
     ['v115@9gywzhi0A8wwR4ilRpg0A8R4A8glBtRpG8BtB8JeAg?WaAY+nABFbcRAyv78Aw3CwBFbUEDPNUPCpOBAA9gzhi0ilA?8Rpywg0glR4A8RpA8wwBtR4G8BtB8JeAAPaA3/35AFbcRAy?v78Aw3CwBFbUEDTHWWCK+AAA9gywhlzhAtA8wwR4glRpg0B?tA8R4A8glRpg0AtG8h0B8JeAAPaA35HOBFbcRAyv78Aw3Cw?BFbUOCPtjWCpOBAA9gywhli0RpA8wwR4glBtg0RpA8R4A8g?lzhG8BtB8JeAAPaAV+f2AFbcRAyv78Aw3CwBFb8KCTHUFDq?OBAA']),
    ('ilo-100', 'ILO', 'I', 'I<L L<O',
     'v115@FfBtCeilBeg0BtBeglRpQ4Aei0CeRpR4zhAeD8Q4Te?RpCeQ4BtBeRpglBeR4BtAeilCeQ4i0zhAeD8g0TeRpCei0B?eRpglBeBtg0Q4AeilCeBtR4zhAeD8Q4JeAgWOApr78AwNUA?BjSUABDHBAAFfBPCeiWBegHBPBegWxSwDAeiHCexSxDTaAe?DAwDTexSCewDBPBexSgWBexDBPAeiWCewDiHTaAeDAgHqey?wHewwOeAAARhxwCeilBexwg0BeBtglwhKeAAPOAprDfETYk?2ARYcRAyfAAA',
     ['v115@9gRpywBthlwhRpQ4wwh0BtglwhB8R4g0C8glwhC8Q4?g0D8whJeAgWbARY0vAwno2AFrnRASoTABBoo2ApvTWCaH2B?A9gRpi0BthlwhRpQ4ywBtglwhB8R4wwC8glwhC8Q4g0D8wh?JeAAPaAWBIOBFbcRAyv78Aw3CwBFb8KCzijxCv/AAA']),
    ('li-100', 'LI', 'I', 'L<I L<J',
     'v115@ygwhIewhCeAtEewhRpBtBei0whRpAtCeR4g0glD8Ae?R4ilJeAgWUAJt78AQSUABDO88A4n4KBKoAVBUhywHewwOeA?AAGhQ4IeQ4CeAtEeQ4xwBtBeilQ4JeAAPOAJtDfETYk2ARY?cRAyfAAA',
     ['v115@9gilR4zhA8glwwR4h0AtRpA8ywA8g0BtRpE8g0AtD8?JeAg0HAv3/wCT+jBA9gxhQahHAeywAewhgWQLgWRaAewhQp?AeySAeQaRpxhEewhQpNeAg0HAzXExCvPdBA9ghlAth0QpgW?BPAeQpglwwglhWBeAPAeCtAeAPhHwSgWEeBPNeAg0HAp/Lg?CaN2BALhhWxSFehlRpVeAg0HAv/7LCzuDCA9gRaAehWRpxh?BeQawSgWyhglwhEeQagWxSQaEeBtNeAg0HApvKWC6+zBA9g?RazSQaRpAeQLxSAPhlQphlAexSAPAeglh0AtwwUeAg0HAzu?bMCv/jBA', 'v115@9gglQ4i0zhA8glR4ywAtRpA8hlQ4A8wwBtRpE8g0At?D8JeAgWaAyCwKBFbcRAyv78Aw3CwBFbMfC6OstCK+AAA']),
    ('other-100-1', 'Other', 'I', 'O<I L<J',
     'v115@3gg0Iei0CezhglQ4CeAtRpilR4AeBtRpD8Q4AeAtKe?AgHNhywHewwVeAgHLhglIeilCexwDewhAeAtKeAgWAA',
     ['v115@9gh0hlywR4whg0RpglA8wwR4Atwhg0RpglC8BtwhG8?AtA8whJeAg0HApHztCqC2BA9gAPwSwhAtFeAPBeAtFeAPQa?QpAtZeAg0HApHkPCMH2BA']),
    ('os-100', 'OS', 'S', 'O<S',
     'v115@6gQ4IeR4whA8hlh0CeQ4whB8glg0BtAeRpwhAeA8gl?g0AeBtRpwhJeAgHMhywHewwWeAgHOhwhIexhQ4Beg0glAeB?txwQ4JeAgH',
     ['v115@9gwhglQ4ywh0RpwhglR4wwAtg0A8RpwhhlQ4Btg0C8?whC8AtE8JeAg0HAJtPFDvC2BA/gQLwShlFegWAeglFeRpgW?ZeAg0HAp+jFDvifBA', 'v115@9gwhBtywR4Rpwhg0BtwwR4A8Rpwhi0ilC8whC8glE8?JeAg0HApintCvX2BA']),
    ('so-100', 'SO', 'S', 'S<O',
     'v115@2gRpEewhBeRpEewhCeR4Bthlwhg0AeR4B8Btglwhi0?B8CeglJeAgWLAz3hRASIrSAzkqBAIhywHewwaeAAAKhxwEe?Q4BexwEeQ4ilEeg0JeAAPPAz3hRA1dk2AwZk2AFrvAA',
     ['v115@9gQ4hlzhywR4glB8Rpg0wwAtA8Q4glB8Rpg0BtF8h0?AtA8JeAg0HA6vytCsedBA9gQaBtDewShWxSAtBeRaAPgWQa?AewSglBehlQaRpFeQawhQpKeAg0HAzurgCMefBA9gCPDeAt?RpgWQawSBewwilQpAeRaBehlAehWFeglxSKeAg0HAU9aFDK?+jBA9gxhAtDeSawhAeQpFeAPAeRpDeySTeAg0HAMtPFDved?BAEhySFexhAeglGeQphlGegWLeAg0HAaNmPCvSdBA9gRpEe?SpxhCeAPgWhlgWAehWBeBPwShWGewwwhKeAg0HAMnLuCp/1?BA']),
    ('oj-and-zs-100', 'OJ+ZS', 'J', 'O<J Z<S',
     'v115@8gwhg0Fehlwhi0R4CeglwhRpR4BtAeA8glwhRpCeBt?C8JeAgWTAsPfRASIiSAzUXSAyU7SAzkzBAMhywHewwWeAAA?QhQ4glFeh0Q4xwCeBtMeAAPPAsPfRA1dk2AwZk2AFrvAA',
     ['v115@9gQ4Bti0zhR4Btwwg0ilB8Q4RpxwglE8RpwwE8JeAg?WaA3/XHBFbcRAyv78Aw3CwBFbMfC0yjFDp/AAA9gRpQ4i0z?hRpR4wwg0ilB8BtQ4xwglE8BtwwE8JeAAPaA25HOBFbcRAy?v78Aw3CwBFbUED0yytCp/AAA9gQ4BtRpwwzhR4BtxwilB8Q?4g0RpwwglE8i0E8JeAAPaA0FAEBFbcRAyv78Aw3CwBFbUOC?s+jFDP+AAA9gRpilwwh0R4RpBtxwg0R4B8zhwwg0E8glBtE?8JeAAPaAU4f2AFbcRAyv78Aw3CwBFb8KCz/lFDvCBAA']),
    ('oj-and-sz-9833', 'OJ+SZ', 'J', 'O<J S<Z',
     'v115@0gg0GewhAeg0Eehlwhh0Q4BtCeglwhRpR4BtAeA8gl?whRpAeQ4CeC8JeAg0TAsfhRASIiSAzUXSAykrSAzUDCAMhy?wHewwWeAAAIhglGeQ4AeglEeh0Q4xwAewhPeAAPRAsfhRA1?dk2AwlGwAzs78AVAAAA',
     ['v115@9gh0whRpilR4g0A8whRpglwwR4A8g0A8whBtxwE8wh?A8BtwwC8JeAgWaAY7fRBFbcRAyv78Aw3CwBFbUEDUubgCqC?BAA9gh0BtzhR4g0A8wwBthlR4A8g0A8xwRpglE8wwA8Rpgl?C8JeAAPaAXEIOBFbcRAyv78Aw3CwBFbMfCs+jFDK+AAA']),
    ('jo-9298', 'JO', 'J', 'J<O',
     'v115@AhhlAeAtBewhQ4CeglBtRpwhR4AeA8glAtg0RpwhAe?Q4AeC8i0whJeAgWLAsvjRAS4WSAzkqBAIhywHewwaeAAAUh?h0AeAtBeQ4AewhDeilQ4JeAAPRAsvjRA1dk2AwF5vAZ078A?VAAAA',
     ['v115@9gwhilR4Ati0whglwwR4BtRpg0whxwB8AtA8RpA8wh?A8wwG8JeAgWaAX7fRBFbcRAyv78Aw3CwBFbMfCpuLuCqCBA?A9gzhR4Ati0wwhlR4BtRpg0xwglB8AtA8RpA8wwA8glG8Je?AAPaA18f2AFbcRAyv78Aw3CwBFbMfC0iLuCK+AAA9gwhwwh?0R4AtglRpwhxwR4BtglRpwhwwg0B8AtA8hlA8whA8g0G8Je?AAPaA08nABFbcRAyv78Aw3CwBFb8KCMnLuC0/AAA9gzhR4B?tRph0wwR4ilRpg0xwB8glA8BtA8g0A8wwG8JeAAPaAz8nAB?FbcRAyv78Aw3CwBFbEwCK3TWCa+AAA9gwhwwh0R4BtRpwhx?wR4ilRpwhwwg0B8glA8BtA8whA8g0G8JeAAPaASEwKBFbcR?Ayv78Aw3CwBFb8KCPNExC6/AAA']),
    ('extra-t-9663', 'T', 'T', '',
     'v115@xfglGeR4glDewhAeR4AthlBeg0whRpBtA8Ceg0whRp?AtC8Aeh0whXeglGeRpglDewhAeAtRphlBeg0whBtR4A8Ceg?0whAtR4C8Aeh0whJeAgWBA0AAAAxfgWGexDgWDeQaAexDAP?hWBegHQaxSBPAACegHQaxSAPCAAehHQa2eywHewwMeAAALh?g0Gexwg0DeQ4AeAtxwh0BeglQ4JeAAPPAUYHDBQY8UBW15A?BFrvAA',
     ['v115@9gwhh0R4Rpywwhg0R4A8Rpilwhg0C8BtglwwA8whE8?BtB8JeAgWaAWBIOBFbcRAyv78Aw3CwBFbUEDpyytCqOBAA9?gwhh0R4Rpilwhg0R4A8Rpywwhg0C8BtglwwA8whE8BtB8Je?AAPaAWBIOBFbcRAyv78Aw3CwBFbUEDp+ytCqCBAA9gywR4z?hAth0R4A8ilBtg0wwC8glRpAtA8g0E8RpB8JeAAPaAzFgRB?FbcRAyv78Aw3CwBFbMfCqXstCU+AAA9gh0ywBtglRpg0R4w?wA8ilRpR4C8zhA8g0E8BtB8JeAAPaATBIOBFbcRAyv78Aw3?CwBFb8KCzvKWC0XBAA9gwhh0R4Btilwhg0R4A8Rpywwhg0C?8RpglwwA8whE8BtB8JeAAPaASEwKBFbcRAyv78Aw3CwBFbM?fCp+jPCsXBAA9gh0ywzhAtg0R4wwA8ilBtR4C8glRpAtA8g?0E8RpB8JeAAPaASBIOBFbcRAyv78Aw3CwBFbMfCzXUPCpOB?AA']),
]
