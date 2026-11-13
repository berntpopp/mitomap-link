--
-- Test fixture: a tiny excerpt of the MITOMAP daily PostgreSQL dump
-- (https://mitomap.org/downloads/mitomap.dump.sql.gz). MITOMAP data are CC BY 3.0;
-- cite MITOMAP: A Human Mitochondrial Genome Database. http://www.mitomap.org
-- Reference abstracts/keywords blanked to keep the fixture minimal.
--
-- PostgreSQL database dump
--

\restrict GB7y5dEmzAqcBdV5nLu083RIgzjAz9nHnWhrf7fHoS7TGpRsyTZPwZtr5tHRMkl

-- Dumped from database version 15.14
-- Dumped by pg_dump version 15.19

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

CREATE FUNCTION mitomap.snvs() RETURNS integer LANGUAGE plpgsql AS $$ begin return 1; end $$;

COPY mitomap.locus (id, name, common_name, starting, ending, strand, type, product, protein_id) FROM stdin;
1	MT-TF	F	577	647	H	t	tRNA phenylalanine	\N
2	MT-RNR1	12S	648	1601	H	r	12S ribosomal RNA	\N
3	MT-TV	V	1602	1670	H	t	tRNA valine	\N
4	MT-RNR2	16S	1671	3229	H	r	16S ribosomal RNA	\N
5	MT-TL1	L(UUA/G)	3230	3304	H	t	tRNA leucine 1	\N
6	MT-ND1	ND1	3307	4262	H	m	NADH Dehydrogenase subunit 1	YP_003024026.1
7	MT-TI	I	4263	4331	H	t	tRNA isoleucine	\N
8	MT-TQ	Q	4329	4400	L	t	tRNA glutamine [on complement]	\N
9	MT-TM	M	4402	4469	H	t	tRNA methionine	\N
10	MT-ND2	ND2	4470	5511	H	m	NADH dehydrogenase subunit 2	YP_003024027.1
11	MT-TW	W	5512	5579	H	t	tRNA tryptophan	\N
12	MT-TA	A	5587	5655	L	t	tRNA alanine [on complement]	\N
13	MT-TN	N	5657	5729	L	t	tRNA asparagine [on complement]	\N
14	MT-TC	C	5761	5826	L	t	tRNA cysteine [on complement]	\N
15	MT-TY	Y	5826	5891	L	t	tRNA tyrosine [on complement]	\N
16	MT-CO1	COI	5904	7445	H	m	Cytochrome c oxidase subunit I	YP_003024028.1
17	MT-TS1	S(UCN)	7446	7514	L	t	tRNA serine 1 [on complement]	\N
18	MT-TD	D	7518	7585	H	t	tRNA aspartic acid	\N
19	MT-CO2	COII	7586	8269	H	m	Cytochrome c oxidase subunit II	YP_003024029.1
20	MT-TK	K	8295	8364	H	t	tRNA lysine	\N
21	MT-ATP8	ATPase8	8366	8572	H	m	ATP synthase F0 subunit 8	YP_003024030.1
22	MT-ATP6	ATPase6	8527	9207	H	m	ATP synthase F0 subunit 6	YP_003024031.1
23	MT-CO3	COIII	9207	9990	H	m	Cytochrome c oxidase subunit III	YP_003024032.1
24	MT-TG	G	9991	10058	H	t	tRNA glycine	\N
25	MT-ND3	ND3	10059	10404	H	m	NADH dehydrogenase subunit 3	YP_003024033.1
26	MT-TR	R	10405	10469	H	t	tRNA arginine	\N
27	MT-ND4L	ND4L	10470	10766	H	m	NADH dehydrogenase subunit 4L	YP_003024034.1
28	MT-ND4	ND4	10760	12137	H	m	NADH dehydrogenase subunit 4	YP_003024035.1
29	MT-TH	H	12138	12206	H	t	tRNA histidine	\N
30	MT-TS2	S(AGY)	12207	12265	H	t	tRNA serine2	\N
31	MT-TL2	L(CUN)	12266	12336	H	t	tRNA leucine2	\N
32	MT-ND5	ND5	12337	14148	H	m	NADH dehydrogenase subunit 5	YP_003024036.1
33	MT-ND6	ND6	14149	14673	L	m	NADH dehydrogenase subunit 6 [on complement]	YP_003024037.1
34	MT-TE	E	14674	14742	L	t	tRNA glutamic acid [on complement]	\N
35	MT-CYB	Cytb	14747	15887	H	m	Cytochrome b	YP_003024038.1
36	MT-TT	T	15888	15953	H	t	tRNA threonine	\N
37	MT-TP	P	15956	16023	L	t	tRNA proline [on complement]	\N
38	MT-HV2	CR:HVS2	57	372	N	n	Hypervariable segment 2 [classic:73-340 ]	\N
39	MT-OHR	CR:OH	110	441	H	n	H-strand origins	\N
40	MT-CSB1	CR:CSB1	213	235	N	n	Conserved sequence block 1	\N
41	MT-TFX	CR:TFX	233	260	N	n	mtTF1 binding site	\N
42	MT-TFY	CR:TFY	276	303	N	n	mtTF1 binding site	\N
43	MT-CSB2	CR:CSB2	299	315	N	n	Conserved sequence block 2	\N
44	MT-HPR	CR:HPR	317	321	N	n	replication primer	\N
45	MT-CSB3	CR:CSB3	346	363	N	n	Conserved sequence block 3	\N
46	MT-4H	CR:mt4H	371	379	H	n	mt4 H-strand control element	\N
47	MT-3H	CR:mt3H	384	391	H	n	mt3 H-strand control element	\N
48	MT-LSP	CR:PL	392	435	L	n	L-strand promoter [on complement]	\N
49	MT-TFL	CR:mtTF1	418	445	N	n	mtTF1 binding site	\N
50	MT-TFH	CR:TFH	523	550	N	n	mtTF1 binding site	\N
51	MT-HSP1	CR:PH1	545	567	H	n	Major H-strand promoter	\N
52	MT-HSP2	PH2	645	645	H	n	Minor H-strand promoter	\N
53	MT-RNR3	-	3206	3229	N	n	5S-like sequence	\N
54	MT-TER	-	3229	3256	N	n	Transcription terminator	\N
55	MT-NC1	NC1	3305	3306	N	n	non-coding nucleotides	\N
56	MT-NC2	NC2	4401	4401	N	n	non-coding nucleotides	\N
57	MT-NC3	NC3	5580	5586	N	n	non-coding nucleotides	\N
58	MT-NC4	NC4	5656	5656	N	n	non-coding nucleotides	\N
59	MT-OLR	OL	5721	5798	L	n	L-strand origin [on complement]	\N
60	MT-NC5	NC5	5892	5903	N	n	non-coding nucleotides	\N
61	MT-NC6	NC6	7515	7517	N	n	non-coding nucleotides	\N
62	MT-NC7	NC7	8270	8294	N	n	non-coding nucleotides	\N
63	MT-NC8	NC8	8365	8365	N	n	non-coding nucleotide	\N
64	MT-NC9	NC9	14743	14746	N	n	non-coding nucleotides	\N
65	MT-ATT	ATT	15925	499	N	n	membrane attachment site	\N
66	MT-NC10	NC10	15954	15955	N	n	non-coding nucleotides	\N
67	MT-CR	CR:Control Region	16024	576	N	n	entire Control Region (including displacement loop)	\N
68	MT-HV1	CR:HVS1/HV1	16024	16383	N	n	Hypervariable segment 1 [classic:16024-16365]	\N
69	MT-7SDNA	CR:7S-like	16106	191	N	n	7S DNA	\N
70	MT-TAS	CR:TAS	16157	16172	N	n	termination-associated sequence	\N
71	MT-5	CR:mt5	16194	16208	N	n	control element	add 16,197 (Ori-b)
72	MT-3L	CR:mt3L	16499	16506	L	n	L-strand control element [on complement]	\N
73	MT-HV3	CR:HVS3	438	574	N	n	Hypervariable segment 3	\N
74	MT-TAS2	CR:TAS2	16081	16138	N	n	extended termination-associated sequence	\N
75	MT-OHR57	CR:OH57	57	57	H	n	H-strand origin	\N
76	MT-HN	Humanin	2633	2707	H	mdp	Humanin peptide (MAPRGFSCLLLLTSEIDLPVKRRA) [MDP]	\N
77	MT-MOTSc	MOTS-C	1343	1393	H	mdp	MOTS-C peptide (MRWQEMGYIFYPRKLR) [MDP]	KP715230.1
78	MT-SHLP1	SHLP1	2485	2559	L	mdp	Small HN-like peptide 1 (MCHWAGGASNTGDARGDVFGKQAG) [MDP on complement]	KX067779.1
79	MT-SHLP2	SHLP2	2088	2168	L	mdp	Small HN-like peptide 2 (MGVKFFTLSTRFFPSVQRAVPLWTNS) [MDP on complement]	KX067780.1
80	MT-SHLP3	SHLP3	1703	1819	L	mdp	Small HN-like peptide 3 (MLGYNFSSFPCGTISIAPGFNFYRLYFIWVNGLAKVVW)  [MDP on complement]	KX067781.1
81	MT-SHLP4	SHLP4	2442	2522	L	mdp	Small HN-like peptide 4 (MLEVMFLVNRRGKICRVPFTFFNLSL) [MDP on complement]	KX067782.1
82	MT-SHLP5	SHLP5	2780	2854	L	mdp	Small HN-like peptide 5 (MYCSEVGFCSEVAPTEIFNAGLVV) [MDP on complement]	KX067783.1
83	MT-SHLP6	SHLP6	2990	3052	H	mdp	Small HN-like peptide 6 (MLDQDIPMVQPLLKVRLFND)  [MDP]	KX067784.1
84	MT-ALTND4	ALTND4	11557	11856	H	mdp	Microprotein (99AA) within MT-ND4 [MDP]	\N
85	MT-SHMOOSE	SHMOOSE	12234	12410	H	mdp	Microprotein (58AA) overlapping MT-TS2, MT-TL1, MT-ND5  [MDP]	\N
86	MT-CYTB-187AA	CYTB-187AA	14833	15396	H	mdp	Protein (187AA) in alternate reading frame of MT-CYB [MDP]	corrected position 5/9/2026 per Hu'24
87	MT-GAU	Gau	6287	6589	L	mdp	Mito derived protein (100AA) within MT-CO1 [MDP on complement]	\N
\.

COPY mitomap.mmutation (id, locus, dz, allele, "position", refna, regna, aa, cons, contr, homo, hetero, status, cfrm_date) FROM stdin;
571	MT-CR	Protective factor for stroke risk (hg V)	m.72T>C	72	T	C	noncoding	\N	1116/61168	nr	nr	Reported	\N
5	MT-ND1	LHON	m.3460G>A	3460	G	A	A52T	M	<0.2	+	+	Cfrm [P]	2023.04.25
279	MT-ND2	Exercise intolerance (EXIT)	m.5133_5134del	5133	AA	:	frameshift	na	.	nr	nr	Reported [VUS]	\N
27	MT-ATP6	NARP / Leigh Disease / MILS / ATP6/8 deficiency / other	m.8993T>C	8993	T	C	L156P	97.78%	2/54594 both patients	-	+	Cfrm [P]	2022.04.13
526	MT-ATP6	Developmental delay & myopathy	m.8993TG>CA	8993	TG	CA	L156P	.	.	+	+	Cfrm [LP]	2024.08.27
26	MT-ATP6	NARP / Leigh Disease / MILS / ATP6/8 deficiency / other	m.8993T>G	8993	T	G	L156R	97.78%	6/54594 all patients	+	+	Cfrm [P]	2022.04.13
29	MT-ATP6	FBSN / Leigh Disease / Spinocerebellar Ataxia / ATP6/8 deficiency	m.9176T>C	9176	T	C	L217P	100%	3/52366	+	+	Cfrm [P]	2022.04.13
30	MT-ATP6	Leigh Disease / Spastic Paraplegia / Spinocerebellar Ataxia / ATP6/8 deficiency	m.9176T>G	9176	T	G	L217R	100%	1/52366	+	+	Cfrm [LP]	2022.08.11
41	MT-ND4	LHON / Progressive Dystonia	m.11778G>A	11778	G	A	R340H	H	<0.2	+	+	Cfrm [P]	2022.08.11
\.

COPY mitomap.rtmutation (id, locus, dz, allele, "position", refna, regna, rna, cons, contr, homo, hetero, status, cfrm_date) FROM stdin;
16	MT-TL1	MELAS / Leigh Syndrome / DMDF / MIDD / SNHL / CPEO / MM / FSGS / ASD / Cardiac+multi-organ dysfunction	A3243G	3243	A	G	tRNA Leu (UUR)	97.78%	9/51192	-	+	Cfrm [P]	2020.07.29
18	MT-TL1	MM / MELAS / SNHL / CPEO	A3243T	3243	A	T	tRNA Leu (UUR)	H	<.02	-	+	Cfrm [LP]	2022.10.10
76	MT-TK	MERRF; Other - LD / depressive mood disorder / leukoencephalopathy / HiCM / lipomas	A8344G	8344	A	G	tRNA Lys	37.78%	4/54594	-	+	Cfrm [P]	2021.11.03
\.

COPY mitomap.polymorphism (id, "position", refna, regna, aachange) FROM stdin;
137110	8860	A	C	T-P
806	8860	A	G	T-A
160146	8860	A	T	T-S
206066	72	T	:	non-coding
11	72	T	A	non-coding
990042	72	TA	:	non-coding
170037	72	TAT	:	non-coding
12	72	T	C	non-coding
13	72	T	G	non-coding
170036	72	T	TG	non-coding
140776	73	A	:	non-coding
130015	73	A	C	non-coding
14	73	A	G	non-coding
170038	73	A	T	non-coding
140794	263	A	:	non-coding
160280	263	A	C	non-coding
87	263	A	G	non-coding
170189	263	A	T	non-coding
991087	3243	A	C	tRNA
991518	5133	A	G	N-D
627	5133	A	T	N-Y
992385	8344	A	T	tRNA
\.

COPY mitomap.mmutation_reference (mmutation_id, reference_id) FROM stdin;
41	593
41	611
41	508
26	185
5	209
5	296
5	196
26	2023080302
26	79
27	99
27	457
29	1021
27	2381
29	1659
29	1693
30	3335
30	3336
30	90767
279	4132
279	91671
279	91672
526	92466
571	92732
526	2025110302
\.

COPY mitomap.rtmutation_reference (rtmutation_id, reference_id) FROM stdin;
76	597
76	493
16	135
16	77
16	115
76	147
18	1935
18	90512
18	90824
\.

COPY mitomap.polymorphism_reference (polymorphism_id, reference_id) FROM stdin;
11	968
12	132
12	263
12	394
13	3082
13	20429
13	90494
14	4
14	140
14	233
87	4
87	26
87	132
627	3612
806	11
806	44
806	45
130015	99016
137110	91660
140776	20140325
140794	20140325
160146	20160620
160280	20160620
170036	20170404
170037	20170404
170038	20170404
170189	20170404
206066	20200901
990042	10433
991087	10433
991518	10433
992385	10433
\.

COPY mitomap.reference (id, authors, title, publication, editors, volume, number, pages, date, city, publisher, keywords, abstract, nlmid) FROM stdin;
4	Aquadro, C.F., Greenberg, B.D.	Human mitochondrial DNA variation and evolution: analysis of nucleotide sequences from seven individuals	Genetics	.	103	2	287-312	1983	.	.	\N	\N	6299878
11	Ballinger, S.W., Schurr, T.G., Torroni, A., Gan, Y.Y., Hodge, J.A., Hassan, K., Chen, K.H., Wallace, D.C.	Southeast Asian mitochondrial DNA analysis reveals genetic continuity of ancient mongoloid migrations [published erratum appears in Genetics 1992 Apr;130(4):957]	Genetics	.	130	1	139-152	1992	.	.	\N	\N	1346259
135	Goto, Y., Nonaka, I., Horai, S.	A mutation in the tRNALeu(UUR) gene associated with the MELAS subgroup of mitochondrial encephalomyopathies	Nature	.	348	6302	651-653	1990	.	.	\N	\N	2102678
26	Bodenteich, A., Mitchell, L.G., Merril, C.R.	A lifetime of retinal light exposure does not appear to increase mitochondrial mutations	Gene	.	108	2	305-310	1991	.	.	\N	\N	1836195
44	Brown, M.D., Voljavec, A.S., Lott, M.T., MacDonald, I., Wallace, D.C.	Leber's hereditary optic neuropathy: a model for mitochondrial neurodegenerative diseases	FASEB Journal	.	6	10	2791-2799	1992	.	.	\N	\N	1634041
45	Brown, M.D., Voljavec, A.S., Lott, M.T., Torroni, A., Yang, C.-C., Wallace, D.C.	Mitochondrial DNA complex I and III mutations associated with Leber's hereditary optic neuropathy	Genetics	.	130	1	163-173	1992	.	.	\N	\N	1732158
77	Ciafaloni, E., Ricci, E., Servidei, S., Shanske, S., Silvestri, G., Manfredi, G., Schon, E. A., DiMauro, S.	Widespread tissue distribution of a tRNALeu(UUR) mutation in the mitochondrial DNA of a patient with MELAS syndrome	Neurology	.	41	10	1663-1665	1991	.	.	\N	\N	1922812
79	Ciafaloni, E., Santorelli, F.M., Shanske, S., Deonna, T., Roulet, E., Janzer, C., Pescia, G., DiMauro, S.	Maternally inherited Leigh syndrome	Journal of Pediatrics	.	122	3	419-422	1993	.	.	\N	\N	8095070
99	De Vries, D.D., Van Engelen, B.G., Gabreels, F.J., Ruitenbeek, W., Van Oost, B.A.	A second missense mutation in the mitochondrial ATPase 6 gene in Leigh's syndrome	Annals of Neurology	.	34	3	410-412	1993	.	.	\N	\N	8395787
115	Enter, C., Muller-Hocker, J., Zierz, S., Kurlemann, G., Pongratz, D., Forster, C., Obermaier-Kusser, B., Gerbitz, K. D.	A specific point mutation in the mitochondrial genome of Caucasians with MELAS	Human Genetics	.	88	2	233-266	1991	.	.	\N	\N	1684568
132	Gill, P., Ivanov, P.L., Kimpton, C., Piercy, R., Benson, N., Tully, G., Evett, I., Hagelberg, E., Sullivan, K.	Identification of the remains of the Romanov family by DNA analysis	Nature Genetics	.	6	2	130-135	1994	.	.	\N	\N	8162066
140	Greenberg, B.D., Newbold, J.E., Sugino, A.	Intraspecific nucleotide sequence variability surrounding the origin of replication in human mitochondrial DNA	Gene	.	21	40545	33-49	1983	.	.	\N	\N	6301949
147	Hammans, S.R., Sweeney, M.G., Brockington, M., Morgan-Hughes, J.A., Harding, A.E.	Mitochondrial encephalopathies: molecular genetic diagnosis from blood samples	Lancet	.	337	8753	1311-1313	1991	.	.	\N	\N	1674297
185	Holt, I.J., Harding, A.E., Petty, R.K., Morgan-Hughes, J.A.	A new mitochondrial disease associated with mitochondrial DNA heteroplasmy	American Journal of Human Genetics	.	46	3	428-433	1990	.	.	\N	\N	2137962
196	Howell, N., Bindoff, L. A., McCullough, D. A., Kubacka, I., Poulton, J., Mackey, D., Taylor, L., Turnbull, D. M.	Leber hereditary optic neuropathy: identification of the same mitochondrial ND1 mutation in six pedigrees	American Journal of Human Genetics	.	49	5	939-950	1991	.	.	\N	\N	1928099
209	Huoponen, K., Vilkki, J., Aula, P., Nikoskelainen, E.K., Savontaus, M.L.	A new mtDNA mutation associated with Leber hereditary optic neuroretinopathy	American Journal of Human Genetics	.	48	6	1147-1153	1991	.	.	\N	\N	1674640
233	Ginther, C., Corach, D., Penacino, G.A., Rey, J. A., Carnese, F. R., Hutz, M. H., Anderson A., Just, J., Salzano, F. M., King, M. C.	Genetic variation among the Mapuche Indians from the Patagonian region of Argentina: mitochondrial DNA sequence variation and allele frequencies of several nuclear genes	EXS	.	67	-	211-219	1993	.	.	\N	\N	8400690
263	Kobayashi, Y., Momoi, M. Y., Tominaga, K., Shimoizumi, H., Nihei, K., Yanagisawa, M., Kagawa, Y., Ohta, S.	Respiration-deficient cells are caused by a single point mutation in the mitochondrial tRNALeu(UUR) gene in mitochondrial myopathy, encephalopathy, lactic acidosis, and stroke-like episodes (MELAS)	American Journal of Human Genetics	.	49	3	590-599	1991	.	.	\N	\N	1715668
296	Majander, A., Huoponen, K., Savontaus, M.L., Nikoskelainen, E., Wikstrom, M.	Electron transfer properties of NADH:ubiquinone reductase in the ND1/3460 and the ND4/11778 mutations of the Leber hereditary optic neuroretinopathy (LHON)	FEBS Letters	.	292	40545	289-292	1991	.	.	\N	\N	1959619
394	Ozawa, T., Tanaka, M., Ino, H., Ohno, K., Sano, T., Wada, Y., Yoneda, M., Tanno, Y., Miyatake, T., Tanaka, T., Itoyama, S., Ikebe, S., Hattori, N., Mizuno, Y.	Distinct clustering of point mutations in mitochondrial DNA among patients with mitochondrial encephalomyopathies and with Parkinson's disease	Biochemical and Biophysical Research Communications	.	176	2	938-946	1991	.	.	\N	\N	2025303
457	Santorelli, F.M., Shanske, S., Jain, K.D., Tick, D., Schon, E.A., DiMauro, S.	A T-C mutation at nt 8993 of mitochondrial DNA in a child with Leigh syndrome	Neurology	.	44	5	972-974	1994	.	.	\N	\N	8190310
493	Shoffner, J. M., Lott, M. T., Lezza, A. M., Seibel, P., Ballinger, S. W., Wallace, D. C.	Myoclonic epilepsy and ragged-red fiber disease (MERRF) is associated with a mitochondrial DNA tRNALys mutation	Cell	.	61	6	931-937	1990	.	.	\N	\N	2112427
508	Singh, G., Lott, M.T., Wallace, D.C.	A mitochondrial DNA mutation as a cause of Leber's hereditary optic neuropathy	New England Journal of Medicine	.	320	20	1300-1305	1989	.	.	\N	\N	2566116
593	Wallace, D.C., Singh, G., Lott, M.T., Hodge, J.A., Schurr, T.G., Lezza, A.M., Elsas, L.J., Nikoskelainen, E.K.	Mitochondrial DNA mutation associated with Leber's hereditary optic neuropathy	Science	.	242	4884	1427-1430	1988	.	.	\N	\N	3201231
597	Wallace, D.C., Zheng, X., Lott, M.T., Shoffner, J.M., Hodge, J.A., Kelley, R.I., Epstein, C.M., Hopkins, L.C.	Familial mitochondrial encephalomyopathy (MERRF): Genetic, pathophysiological, and biochemical characterization of a mitochondrial DNA disease	Cell	.	55	4	601-610	1988	.	.	\N	\N	3180221
611	Yoneda, M., Tsuji, S., Yamauchi, T., Inuzuka, T., Miyatake, T., Horai, S., Ozawa, T.	Mitochondrial DNA mutation in family with Leber's hereditary optic neuropathy	Lancet	.	1	8646	1076-1077	1989	.	.	\N	\N	2566021
968	Mountain, J.L., Hebert, J.M., Bhattacharyya, S., Underhill, P.A., Ottolenghi, C., Gadgil, M., Cavalli-Sforza, L.L.	Demographic history of India and mtDNA-sequence diversity	American Journal of Human Genetics	.	56	4	979-992	1995	.	.	\N	\N	7717409
1021	Thyagarajan, D., Shanske, S., Vazquez-Memije, M., De Vivo, D., DiMauro, S.	A novel mitochondrial ATPase 6 point mutation in familial bilateral striatal necrosis	Annals of Neurology	.	38	3	468-472	1995	.	.	\N	\N	7668837
1659	Campos, Y., Martin, M.A., Rubio, J.C., Solana, L.G., Garcia-Benayas, C., Terradas, J.L., Arenas, J.	Leigh syndrome associated with the T9176C mutation in the ATPase 6 gene of mitochondrial DNA	Neurology	.	49	2	595-597	1997	.	.	\N	\N	9270604
1693	Dionisi-Vici, C., Seneca, S., Zeviani, M., Fariello, G., Rimoldi, M., Bertini, E., De Meirleir, L.	Fulminant Leigh syndrome and sudden unexpected death in a family with the T9176C mutation of the mitochondrial ATPase 6 gene	Journal of Inherited Metabolic Disease	.	21	1	2-8	1998	.	.	\N	\N	9501263
1935	Shaag, A., Saada, A., Steinberg, A., Navon, P., Elpeleg, O. N.	Mitochondrial encephalomyopathy associated with a novel mutation in the mitochondrial tRNA(leu)(UUR) gene (A3243T)	Biochemical and Biophysical Research Communications	.	233	3	637-639	1997	.	.	\N	\N	9168904
2381	DiMauro, S., De Vivo, D. C.	Genetic heterogeneity in Leigh syndrome	Annals of Neurology	.	40	1	5-7	1996	.	.	\N	\N	8687192
3082	Dimo-Simonin, N., Grange, F., Taroni, F., Brandt-Casadevall, C., Mangin, P.	Forensic evaluation of mtDNA in a population from south west Switzerland	International Journal of Legal Medicine	.	113	2	89-97	2000	.	.	\N	\N	10741483
3335	Carrozzo, R., Murray, J., Santorelli, F. M., Capaldi, R. A.	The T9176G mutation of human mtDNA gives a fully assembled but inactive ATP synthase when modeled in Escherichia coli	FEBS Letters	.	486	3	297-299	2000	.	.	\N	\N	11119722
3336	Carrozzo, R., Murray, J., Capuano, O., Tessa, A., Chichierchia, G., Neglia, M. R., Capaldi, R. A., Santorelli, F. M.	A novel mtDNA mutation in the ATPase6 gene studied by E. coli modeling	Neurological Sciences	.	21	5 Suppl	S983-984	2000	.	.	\N	\N	11382202
3612	Sudoyo, H., Suryadi, H., Lertrit, P., Pramoonjago, P., Lyrawati, D., Marzuki, S.	Asian-specific mtDNA backgrounds associated with the primary G11778A mutation of Leber's hereditary optic neuropathy	Journal of Human Genetics	.	47	11	594-604	2002	.	.	\N	\N	12436196
4132	Schwartz, M., Vissing, J.	Paternal inheritance of mitochondrial DNA	New England Journal of Medicine	.	347	8	576-580	2002	.	.	\N	\N	12192017
10433	Bolze, A., Mendez, F., White, S., Tanudjaja, F., Isaksson, M., Jiang, R., Dei Rossi, A., Cirulli, E. T., Rashkin, M., Metcalf, W. J., Grzymski, J. J., Lee, W., Lu, J. T., Washington, N. L.	A catalog of homoplasmic and heteroplasmic mitochondrial DNA variants in humans, doi:10.1101/798264	bioRxiv	.	\N	new database URL	https://www.helix.com/mitochondrial-variant-database	2020	.	.	\N	\N	\N
20429	Zupanic Pajnic, I., Balazic, J., Komel, R.	Sequence polymorphism of the mitochondrial DNA control region in the Slovenian population	International Journal of Legal Medicine	.	118	1	1-4	2004	.	.	\N	\N	14534795
90494	Brandstatter, A., Sanger, T., Lutz-Bonengel, S., Parson, W., Beraud-Colomb, E., Wen, B., Kong, Q. P., Bravi, C. M., Bandelt, H. J.	Phantom mutation hotspots in human mitochondrial DNA	Electrophoresis	.	26	18	3414-3429	2005	.	.	\N	\N	16167362
90512	Sohm, B., Frugier, M., Brule, H., Olszak, K., Przykorska, A., Florentz, C.	Towards understanding human mitochondrial leucine aminoacylation identity	Journal of Molecular Biology	.	328	5	995-1010	2003	.	.	\N	\N	12729737
90767	Alvarez-Iglesias, V., Barros, F., Carracedo, A., Salas, A.	Minisequencing mitochondrial DNA pathogenic mutations [METHODS]	BMC Medical Genetics	.	9	-	26	2008	.	.	\N	\N	18402672
90824	Longo, N., Schrijver, I., Vogel, H., Pique, L. M., Cowan, T. M., Pasquali, M., Steinberg, G. K., Hedlund, G. L., Ernst, S. L., Gallagher, R. C., Enns, G. M.	Progressive cerebral vascular degeneration with mitochondrial encephalopathy	American Journal of Medical Genetics	.	146	3	361-367	2008	.	.	\N	\N	18203188
91671	Krag, T. O., Hauerslev, S., Jeppesen, T. D., Duno, M., Vissing, J.	Muscle regeneration in mitochondrial myopathies	Mitochondrion	.	13	2	63-70	2013	.	.	\N	\N	23376095
91660	Barbieri, C., Vicente, M., Rocha, J., Mpoloka, S. W., Stoneking, M., Pakendorf, B.	Ancient substructure in early mtDNA lineages of southern Africa	American Journal of Human Genetics	.	92	2	285-292	2013	.	Some reported SNPs are only found in the associated GB sequences or in the supplemental information, not in the body of the paper itself.	\N	\N	23332919
91672	Jeppesen, T. D., Orngreen, M. C., van Hall, G., Haller, R. G., Vissing, J.	Fat metabolism during exercise in patients with mitochondrial disease	Archives of Neurology	.	66	3	365-370	2009	.	.	\N	\N	19273755
92466	Wong, L. C., Chen, T., Schmitt, E. S., Wang, J., Tang, S., Landsverk, M., Li, F., Zhang, S., Wang, Y., Zhang, V. W., Craigen, W. J.	Clinical and laboratory interpretation of mitochondrial mRNA variants	Human Mutation	.	41	10	\N	2020	.	.	\N	\N	32652755
92732	Onieva, A., Martin, J., D, R. C.-A., Planells, V., Coronado-Zamora, M., Beyer, K., Vega, T., Lozano, J. E., Santos, C., Aluja, M. P.	Complete mitochondrial DNA profile in stroke: A geographical matched case-control study in Spanish population	Mitochondrion	.	73	\N	51-61	2023	.	.	\N	\N	37793469
99016	van Oven, M., Kayser, M.	Phylotree	http://www.phylotree.org	.	Variants appear in tree, sequence(s) available. Phylotree	Build 16	19 Feb	2014	.	.	\N	\N	\N
20140325	Sequence listing.	.	Variant has been found in GenBank	.	Sequence or sequences are available	use GB Frequency link to retrieve sequence information	First retrieved from GB on 25 March 2014	2014	.	.	\N	\N	\N
20160620	Sequence listing.	.	Variant has been found in GenBank	.	Sequence or sequences are available.	use GB Frequency link for sequence info	First retrieved from GB on 25 June 2016	2016	.	.	\N	\N	\N
20170404	Sequence listing.	.	Variant has been found in GenBank	.	Sequence or sequences are available.	use GB Frequency link for sequence info	First retrieved from GB on 4 April 2017	2017	.	.	\N	\N	\N
20200901	Sequence listing.	.	Variant has been found in GenBank	.	Sequence or sequences are available.	use GB Frequency link for sequence info	First retrieved from GB on 01 Sept 2020	2020	.	.	\N	\N	\N
2023080302	Mitochondrial Variant Curation Expert Panel (VCEP)	ClinGen Evidence Repository	https://erepo.clinicalgenome.org/evrepo/ui/classification/3d253f8e-0dc8-4828-a473-d6ed6771fb5a	.	VCEP evaluation and approval as VUS	2023.06.26	m.7637G>A (p.E18K) variant in MT-CO2	2023	.	.	\N	\N	\N
2025110302	Mitochondrial Variant Expert Panel Curation	\N	https://erepo.clinicalgenome.org/evrepo/ui/classification/e5b8c0e3-3e07-4d9f-9b74-b3643a059af5	.	VCEP evaluation and approval report [LP]	2024.08.27	m.8993_8994delinsCA (p.Leu156Pro) variant in MT-ATP6	2025	.	.	\N	\N	\N
\.

COPY mitomap.variants_count (tpos, tnt, qnt, ntchange, fl_count, cr_count) FROM stdin;
72	T	:	deletion	1	0
72	T	A	transversion	7	3
72	T	C	transition	1169	659
72	T	G	transversion	50	30
72	T	TG	insertion	0	2
72	TAT	:	deletion	0	2
73	A	:	deletion	1	0
73	A	C	transversion	3	11
73	A	G	transition	50930	43951
73	A	T	transversion	0	3
263	A	:	deletion	1	1
263	A	C	transversion	5	26
263	A	G	transition	64039	47067
263	A	T	transversion	0	3
3243	A	G	transition	10	0
3460	G	A	transition	31	0
5133	A	T	transversion	1	0
8344	A	G	transition	4	0
8860	A	C	transversion	2	0
8860	A	G	transition	66133	0
8860	A	T	transversion	1	0
8993	T	C	transition	2	0
8993	T	G	transversion	6	0
9176	T	C	transition	3	0
9176	T	G	transversion	1	0
11778	G	A	transition	191	0
\.

COPY mitomap.summary (name, count) FROM stdin;
genbank	66775
gbcontrol	81796
SNVs	20024
\.

COPY mitomap.edit_date (id, table_name, date) FROM stdin;
45793	ref	2026-11-10
45794	geneloc	2026-07-13
45795	pheno	2003-06-01
45796	haplo	2003-06-01
45797	polyPep	2004-03-09
45798	polymorph	2026-11-03
45799	mMut	2026-11-09
45800	rtMut	2026-11-03
45801	del	2026-03-09
45802	mDel	2012-05-25
45803	ins	2008-05-02
45804	rearrang	2003-11-21
45805	somat	2026-03-20
45806	unpub	2017-06-30
45807	trans	2003-06-01
45808	codons	2003-06-01
45809	rEnzyme	2003-06-01
45810	rSite	2003-06-01
\.

