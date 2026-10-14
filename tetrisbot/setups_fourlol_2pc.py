"""2nd PC patterns from https://four.lol/perfect-clears/2nd (knewjade's guide).

After a 4-line 1st PC (Jaws, PCO, ...) 4 pieces of bag 2 are left. Each pattern arranges
them on the empty field; then a 4-line PC with the next 6 pieces leaves exactly one
piece over - the DPC extra piece.
Each entry: (name, PC chance %, [fumens]). Pages without grey cells are setups (one per
set of leftover pieces), pages with grey cells are PC solutions (grey = the setup).
Extracted by script from the page data. Mirrors are generated in code.
"""

PATTERNS = [
    ('With T 1', 99.76, [
        'v115@GhwwDeg0CexwDei0BtwwDezhBtJeAgHGhAPDeQaCew?hAPDeRawhQpglAPDeAth0wwglwSJeAAALhwSIewSAehWFew?SQLgWMeAAAPhQaFeRaAeQaGeQagWQaKeAAAGhQpDeQpCeQa?QpDeQpwhQpglQawhDeQpwwQpgWwSwhJeAAA',
        'v115@GhA8DeA8CeB8DeF8DeF8JeAgWIANI98AQPcQB',
        'v115@9gzhywR4A8h0hlA8wwR4B8g0RpglF8g0RpglF8JeAg?0GAv/rtCU+AAA9gyhGeAPgWAtQaFegWwhQpQaFegWRpQaPe?Ag0GApfLuC0CBAA9gQaBtwwRaAehWAeQagWwhwwAeQawSgW?BewSgWwhg0FewSBPg0PeAg0GAzSNFD0/AAA9gwwAeBPxhAe?hlAewwwhBPAewhQpglBewwwhAPQLGeRagHPeAg0GAJ3jPCs?OBAABhRaAehWFeQawSgWfeAg0GAJnzPCsOBAA9gQLwSwhAt?FeQLBeAtFeQLRaHewhxwPeAg0GAMePFDvOBAA+gQpQaAPxh?AehlBeRpBewhQpglCexhHewhwSAPPeAg0GAPujPC0CBAA9g?wwBeSaAehWAewhBPQLAeQawSgWBewwBeQaFewwBeQaPeAg0?GAPejWC0/AAA',
    ]),
    ('With T 2', 97.14, [
        'v115@Ghg0DeglAewwBeg0Deglywh0DehlzhJeAgHBhwwDeg?HDeQpwwQLg0AegHDeQphlwhFexwNeAAABhQLBeAtGeQLAtg?WGegWwSGegWgHCewwJeAAABhQ4BeAPFeglQ4APwhFewhglw?hRaAPDewhxwxhAPJeAAABhgWIehWAewhFeQaAeglwhgWwhD?exhAeAtxhJeAAABhglIehlAeQaFewhAegWQaFeRaAeQaLeA?AABhwDBewwFeQLwDwwGeAPwSQaGeBPgWQaLeAAAEhQaFeQp?AeRaFeQpwhAewSFeQpAehWLeAAABhwhBeAPFeAPglAPwhFe?APwSwhQpFeAPBeQpLeAAAMhQpAewhGeQpAewhGeQpAtwhLe?AAA',
        'v115@GhA8DeA8AeA8BeA8DeF8DeF8JeAgWIANI98AQPcQB',
        'v115@9gilwhywRpA8glAtg0whA8wwA8RpA8Btg0whF8Ath0?whF8JeAg0GApfrgC0CBAA9gQaBtwwFeQagWwhwwFewSgWwh?g0FewSBPg0PeAg0GAzSFgC0/AAA9gg0BPQLFeg0wwRLFexw?QLgHFewwBtgHPeAg0GAKuytCsOBAA9ggHBtQpFegHQaglQp?FeQLQaglwhFeQLBPwhPeAg0GAMuaFDqOBAA+gBPgWHehlGe?gWAeAtHehlPeAg0GAauaPC0CBAA9gwwBtQaFewhBPQLFewh?RpQLFeg0wwglwSPeAg0GATuKWC0/AAA',
    ]),
    ('With T 3', 100.0, [
        'v115@Ohg0DeR4wwBei0AeR4ywzhJeAglZhxSFexwhlJeAAe?ThgWwSQaCeRpAehWAeRaRLhWJeAAeZhxSFexwhlJeAAe',
        'v115@OhA8DeC8BeC8AeI8JeAgWIANI98AQPcQB',
        'v115@9gwhh0R4ywRpwhg0R4BtwwA8Rpwhg0C8BtC8whI8Je?Ag0GAauytCqOBAA+gQagWwSQLwSxhCeQagWwSAegWwhDeQa?CegWglWeAg0GAJn/VC0XBAA',
    ]),
    ('With T 4', 100.0, [
        'v115@JhBtHewwBtR4DeywR4zhJeAgHJhglwhHeyhFexhQeA?AAKhwSIewSAehWFewSQLgWNeAAA',
        'v115@JhB8HeE8DeI8JeAgWIANI98AQPcQB',
        'v115@9gwhh0Btywhlwhg0B8BtwwRpglwhg0E8RpglwhI8Je?Ag0GAP+TFDqOBAAFhxwGeBtHeRaUeAg0GAMujFDqOBAA',
    ]),
    ('With T 5', 99.84, [
        'v115@KhAtFeRpBtR4wwCeRpAtR4ywLeAgHKhwhHexhgWwSQ?aEewShHAPRaLeAAAKhwSFeQpQaxSFeRpwwCtNeAwhVhglQp?whFehlAexhLeAwhKhAtFeAPBeAtRaDeAPRLhHOeAwD',
        'v115@KhA8FeG8CeH8LeAgWIANI98AQPcQB',
        'v115@9gg0zhR4wwhli0A8R4ywglG8BtglH8BtJeAg0GA6C+?tCK+AAA9gwSglyhCeRpxSAPCeRaAeAtIeAtHehlJeAg0GAq?HcgC0CBAAChgWQaxhAPDehWwhQpwhQLGeRpQLHewhQLJeAg?0GAJNegCqCBAADhSLHeQaAewwGexSwwHewSQpJeAg0GA6/d?gCpCBAAChglg0ywDehlAPSLdeAg0GAaubgCs/AAAChgWwSg?WxhDehWAtRpwwGeRpIehlJeAg0GAqurgCMNBAA',
        'v115@9gRpilR4i0RpglA8R4ywAtG8wwBtH8Atg0JeAg0ZAx?Fg2AFbcRAyv78Aw3CwBFbUEDU9KWCqAAAA',
    ]),
    ('Without T 1', 95.0, [
        'v115@LhBthlFeg0BtglRpDei0glRpJeAglLhhlxwGeRpHeB?PMeAAeLhAPAeRaFeAPxSAtFeAPAehlLeAAeMhBPHeRpGexw?hlLeAAAMhxhHeBPAeRpDeTLhWJeAAAMhRaHeBtGexwNeAAA?LhBtglgWFeAtBPhWAPDeQaAPglyhJeAAA',
        'v115@LhD8FeF8DeF8JeAgWIANI98AQPcQB',
        'v115@9gh0R4zhRpg0R4wwD8RpBtxwF8g0BtwwF8JeAg0GA6?uHgCT+AAA9ghWRLFeQaySFexhhlFeQaRpwSPeAg0GAzOMgC?a+AAA9gxhQpglFewhglAeglFewhAewSQLFewhRLQeAg0GAs?vaFDU+AAA9gglBewhFexhhWGeglwhHeBtQeAg0GAqyytCU+?AAA9gQawhxSFeQawSglHegWQaglFeSaQeAg0GA0HbPCM+AA?A9gBPAeQpFeAPAewhQpFegWQaRpFeQahlQpPeAg0GAzXegC?pCBAA9gBtAewSFeAtQpglwSFeRpgWQLFeglhWQeAg0GAU9K?WCK+AAA9gRaQpglFeAPgWwSglFeQLQawhAtFeAPwSQawhPe?Ag0GAsfrgCpOBAA9gglBewhFewwglwhglGeBPHewwglQeAg?0GAqybgCpOBAA',
    ]),
    ('Without T 2', 80.0, [
        'v115@LhAtBeg0EeBtR4g0RpCeAtR4h0RpJeAgHZhRpFeRLh?WJeAAAOhAPGeRLAPxSDehHBehlJeAAA',
        'v115@LhA8BeA8EeG8CeG8JeAgWIANI98AQPcQB',
        'v115@9gwhh0ilR4Rpwhg0wwglA8R4A8RpwhxwG8whg0wwG8?JeAg0GApuHgCzCBAA9gwhAPQLSaDeAtAPwhAtFeAtAewhGe?AtAPwhQeAg0GAqOMgCT+AAA9gCtyhDewhQpQaAPFeSaGewh?glgWQeAg0GAa3TxCqCBAA',
    ]),
    ('Without T 3', 93.33, [
        'v115@NhAtBeg0DeglBtR4g0BeilAtR4h0JeAgHNhgWHehWE?eSawSNeAAA',
        'v115@NhA8BeA8DeF8BeH8JeAgWIANI98AQPcQB',
        'v115@9gzhAtilR4i0BtglA8R4A8Rpg0AtF8RpH8JeAg0GAP?tzPCM+AAA+gxwglQaEeQLAeSaEegWglQawhFegWQpReAg0G?ApuntCvCBAA9gwwAegWGewwgWQaHeCPFewwgWReAg0GAp3n?tCvCBAA',
    ]),
    ('Without T 4', 88.06, [
        'v115@GhwhEeBtBewhDeRpBtglwhDeRpilwhJeAgHGhwwIew?wHeAtwwFeSaKeAAAGhQLFeglBeQLDexhglQawSQLDewhQpw?whlKeAAAMhQpwhGeRpAPGegWBPMeAAAEhg0AeQaGeg0AeQa?FeAtQpAeglDeSagWAeglJeAAA',
        'v115@GhA8EeB8BeA8DeF8DeF8JeAgWIANI98AQPcQB',
        'v115@9gzhilRpA8wwi0glB8RpA8xwR4F8wwR4g0F8JeAg0G?AzuHgCM+AAA9gxwh0FeyhQaFeRahWFewhxSQaPeAg0GA6uH?gCzCBAA9gBPQLgHSaCeAPwSgWAeQpGehlFegWRpQeAg0GAz?XegCpCBAA9gQaCtyhCeQaglBewSEewSAewSgWFewSQawSQa?PeAg0GAauKxCqCBAA9gAtCPSaCeAtQawSwhAtEeAtRpwhFe?g0whgWglPeAg0GAzvKxCM+AAA+gBtwwyhEewwAeAPEeQawS?AewhFegWwSglwhPeAg0GAaNegCs/AAA9gglhWQLSaCehlgW?QaQpEehWQLgWFewSQpAewSPeAg0GAMH+tCa+AAA9ggWSpyh?CehWRawSEeQpBtwhFewwBeglPeAg0GAKHmFDMNBAA9gwhBe?whFehlxhFewhBeQaFehHwSQLPeAg0GAJH+tCs/AAA9gQLRa?GegHQaHeQLAewhglGeh0AtPeAg0GATuaPC0CBAA9gwwgWwh?glFewwAewhGeQpiWFeQpSeAg0GAUn/VCaNBAA',
    ]),
    ('Without T 5', 93.97, [
        'v115@9gwhIewhCeAtEewhRpBtR4CewhRpAtR4NeAgHLhgWF?eQpQahWFeRpglPeAAA',
        'v115@9gA8IeA8CeA8EeG8CeF8NeAgH',
        'v115@9gA8g0zhR4hlA8i0A8R4BtglG8wwBtF8ywglJeAg0G?A0XstCK+AAA+gwSglyhRaAtQaAexSAPAexSQpglQaGeglQp?wSFeRaglQaJeAg0GATergCqCBAADhSLHegWQaAtGeRawwHe?gWwwJeAg0GAqXegCpCBAAOhyhGeSaTeAg0GA03HgCpCBAAD?hywFexhQagWQLGeRaAPFewhAewhQLJeAg0GAa+dgCs/AAAD?hxhgWwwEehlQaAewwHeglwwFeAPwSQLKeAg0GApfLuCvCBA?A',
        'v115@9gA8RpilzhA8RpglA8ywR4G8i0F8wwR4g0JeAgWZAy?FYHBFbcRAyv78Aw3CwBFbUOCz+CMCsAAAA9gA8RpilzhA8R?pglA8ywAtg0G8Btg0F8wwAth0JeAAPZAy5nABFbcRAyv78A?w3CwBFbUOC6+CMCsAAAA',
    ]),
    ('Other 1', 94.21, [
        'v115@GhAtHeBtRpDeR4AtglRpCeR4ilJeAgHGhwSHeglwSH?eglQaGeBtQaJeAAA',
        'v115@9gRpwwhlh0R4A8Rpxwglg0R4D8Btglg0F8wwBtE8Je?AgWGAat/VCUHBAA9gRph0wwzhA8Rpg0xwilD8BtwwglF8g0?BtE8JeAgWGA6CmPCP+AAA9gilzhR4A8glywRpR4D8BtRpF8?wwBtE8JeAgWGAaH+tCpCBAA9gRphlwhh0R4A8Rpwwglwhg0?R4D8xwwhg0F8wwglwhE8JeAgWGAp+jPCMHBAA9gRpBtilR4?A8Rpwwi0R4D8xwglg0F8wwBtE8JeAgWGAUtHgCsXBAA9gRp?h0ilR4A8Rpg0wwglAtR4D8xwBtF8g0wwAtE8JeAgWGA6unt?CvCBAA9gRpwhQ4BtywA8RpwhR4BtwwD8whilF8whglQ4E8J?eAgWGAMujFDvOBAA9gRpBtywR4A8Rpg0BtwwR4D8zhF8i0E?8JeAgWGApvbgC6OBAA9gRpBtywR4A8RpzhR4D8g0BtwwF8i?0E8JeAgWGAK9CMC6OBAA9gi0wwilR4A8zhglAtR4D8xwBtF?8g0wwAtE8JeAgWGAad9VC0/AAA',
    ]),
    ('ILOT', 100.0, [
        'v115@OhglDewwBeilRpAeywzhRpJeAgHOhAtGexwAtFeh0x?wLeAAAZhRpFeRLhWJeAAA',
        'v115@OhA8DeA8BeE8AeI8JeAgWIANI98AQPcQB',
        'v115@9gwhh0ywR4Rpwhg0BtwwR4A8Rpwhg0A8BtE8whI8Je?Ag0GAJNMgC6OBAA+gQaAPwSxhEeQawhgWwhFeQaAegWglYe?AAtGAUt/VCvXBAA',
    ]),
    ('JLOT', 100.0, [
        'v115@HhglEeg0CeglBewwBeg0RpAehlywh0RpKeAgH',
        'v115@9ghlh0ywRpwhA8glg0BtwwA8RpwhA8glg0A8BtC8wh?I8whJeAg0GApHbPCsOBAA9gRpQaAPwSxhDeQpwhQpgWwhEe?wwwhAegWglXeAg0GAJ9aPCsOBAA',
    ]),
    ('STTZ', 98.81, [
        'v115@9gBtHewwBtBewwDexwR4xwDewwR4BewwNeAgH9gwSw?hHeAPxhGeAPIeAPSeAAA',
        'v115@9gB8zhh0R4C8RpA8g0R4wwF8BtxwC8RpA8g0BtwwJe?Ag0GA6+aPCT+AAADhhWRLFeQaySFexhhlFeQaRpwSJeAg0G?Az+KWCa+AAA/gRph0xSRaCeBtAewhglgWGewhgWAPQLCexh?AewhBPKeAg0GAv/rtCa+AAA/gxShHAtywCeBPAeRawwAtFe?gWwhAtwwCeRaAeQaxhwwJeAg0GAa9KxCK+AAADhwSBPQaFe?wSQagWQaPeQaRpgWJeAg0GAzHLxCM+AAA/gRph0QaBewSCe?xhAeRagWwhFewSQaAPQaCeBtAewSQLQawhJeAg0GAKXNFDz?CBAADhwhBeQaCeRpAeglAeQpQLFeglAeQpQLCexSAewhAtA?eQLJeAg0GApvytC6CBAADhxhEexSAeRaAPGeRpEeRpAewhw?SLeAg0GAp/TFDPNBAADhRaIexhHexSGeRpLeAg0GAKuaFDM?NBAADhCtQeAPIeBPLeAg0GApyaFDz/AAADhQLBewwFeQaBe?wwFeQaBewhFeQaAeAPwhJeAg0GAMXNFDKNBAADhwwxSQLCe?RpAewwRpQLFewhSaCexSAeyhQaJeAg0GApintCvXBAAEhRp?GeAPxSHexhHeQaQpKeAg0GApyytC6/AAAFhAPwhFeAtBewh?FeAtBewhFeRaQLKeAg0GAJn/VCzXBAADhRLRaFewSAeQaHe?RpGehlwwwhJeAg0GAqyytCa+AAANhglQaHeRawSwhFeglQa?wSwhJeAg0GAvOstCa+AAANhwhBtQpFehWhlFegWwhQpglJe?Ag0GAvuntCa+AAAKhxSReRpOeAg0GAvuPFDT+AAANhQaBPw?SFehlhWFeglQawSgWJeAg0GAvOUFDT+AAADhhlxhFegWwhQ?pGewhAehlFewhAtQpQaJeAg0GAqOMgCaNBAAKhRpRexSOeA?g0GAqOMgCzXBAADhRpxhCexSAeQpglgWwhFeQaBewSCeRpB?eBPKeAg0GAsuHgCaNBAAKhRpRexSOeAg0GAsuHgCzXBAAFh?QpgWCexSAeQaAeglgWFeySQaCeRpAeAPQpAtQaJeAg0GApC?mFDz/AAADhQLBPwhCeRpAeAPBeAtFeQaBtwwCexSAeQawSQ?awwJeAg0GAK+9tC6CBAADhwwAtAeQaCexSAewhxSAPFewwx?SQLCeRpAewwwhgWQLJeAg0GAP+TFDKNBAADhQLBewhCeRpA?eQaBtwwFeQLBewhCexSAeQLBewhJeAg0GAPentCsXBAADhw?hwSwhAtCexSAewhxSGewhQaQpAtCeRpBehWQaJeAg0GAp/L?gCaNBAAKhRpRexSOeAg0GAp/LgCzXBAADhQahWQLCexSBeh?lQaGeAtEeRpAexhAtwwJeAg0GAs/lFDT+AAAKhRpAeQpBew?hGeBPDexSBeQpwhKeAg0GAqC+tCa+AAADhywAtCexSAehWA?eQaFexhAtQaCeRpAeQaAPRLJeAg0GAJHmFDKNBAADhQaBPw?SFehlhWFeglQawSgWTeAg0GAJHmFDMNBAADhwhBtQpCeRpA?eBPhWFegWwhhlCexSAehlwwAtJeAg0GAPuTxC6/AAAKhxSR?eRpOeAg0GAPejxCz/AAA',
    ]),
]
