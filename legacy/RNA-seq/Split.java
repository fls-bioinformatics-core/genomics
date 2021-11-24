/*
 * Split.java
 *
 * This program takes in two Bowtie SAM files from the same sample mapped to
 * two genomes ("genomeS" and "genomeB").
 *
 * It produces 4 sam files:
 *
 * 1 - reads that map to genomeS only
 * 2 - reads that map to genomeB only
 * 3 - reads that map to genomeS and genomeB keeping the genomeS genome coordinates
 * 4 - reads that map to genomeS and genomeB keeping the genomeB genome coordinates
 *
 * To run e.g. qsub test1 'java Split genomeS.sam genomeB.sam'
 *
 * Author: leo zeef
 * Created: 22/06/2011 13:19:18
 */
import java.io.*;//file input
import java.util.*;	//StringTokenizer

class Split
{
	private String fileNameInSC= "";
	private String fileNameInSB= "";
	private BufferedReader bFReaderSC =null;
	private BufferedReader bFReaderSB =null;
	private StringTokenizer tokenSC;
	private StringTokenizer tokenSB;
	private String [] lineMatrixSC;
	private String [] lineMatrixSB;
	int col = 0;

		
	//constructor
	public Split()
	{
	}
	
	//make string matrix from the data in the file
	 public String getDataFromFile(String fileNameIngenomeS, String fileNameIngenomeB)
	{
		fileNameInSC = fileNameIngenomeS;
		fileNameInSB = fileNameIngenomeB;
		
		try
		{
			//make things to read 2 files and to write 4 files
			bFReaderSC = new BufferedReader (new FileReader (fileNameInSC));	
			bFReaderSB = new BufferedReader (new FileReader (fileNameInSB));
			
			String StringLineSC = bFReaderSC.readLine();
			String StringLineSB = bFReaderSB.readLine();
						
			FileWriter fwSC = new FileWriter ("Split_mapSConly_"+fileNameInSC);
			FileWriter fwSCSB = new FileWriter ("Split_mapSCandSB_"+fileNameInSC);
			FileWriter fwSB = new FileWriter ("Split_mapSBonly_"+fileNameInSB);	
			FileWriter fwSBSC = new FileWriter ("Split_mapSBandSC_"+fileNameInSB);	
			
	      	BufferedWriter bwSC = new BufferedWriter (fwSC);
	      	BufferedWriter bwSCSB = new BufferedWriter (fwSCSB);
	      	BufferedWriter bwSB = new BufferedWriter (fwSB);
	      	BufferedWriter bwSBSC = new BufferedWriter (fwSBSC);
	      	
			PrintWriter outFileSC = new PrintWriter (bwSC);
			PrintWriter outFileSCSB = new PrintWriter (bwSCSB);
			PrintWriter outFileSB = new PrintWriter (bwSB);
			PrintWriter outFileSBSC = new PrintWriter (bwSBSC);
			
			while (StringLineSC != null && StringLineSB != null)
			{
				//do headers first
				while (StringLineSC.substring(0,1).equals("@"))
				{
					outFileSC.print (StringLineSC);	
					outFileSCSB.print (StringLineSC);						
					outFileSC.println ();
					outFileSCSB.println ();
					StringLineSC = bFReaderSC.readLine();
				}	
				
				while (StringLineSB.substring(0,1).equals("@"))
				{
					outFileSB.print (StringLineSB);	
					outFileSBSC.print (StringLineSB);						
					outFileSB.println ();
					outFileSBSC.println ();
					//System.out.println(StringLineSB);
					StringLineSB = bFReaderSB.readLine();
				}
				
				//headers of the files are now done. Now deal with tab delimited data.
				tokenSC = new StringTokenizer (StringLineSC, "\t");
				tokenSB = new StringTokenizer (StringLineSB, "\t");
				lineMatrixSC = new String [15];
				lineMatrixSB = new String [15];
				
				col = 0;
				
				while (tokenSC.hasMoreTokens())
				{
					//System.out.println("test");					
					lineMatrixSC[col] = tokenSC.nextToken();
					col++;
				}
				
				col = 0;
				while (tokenSB.hasMoreTokens())
				{
					//System.out.println("test");					
					lineMatrixSB[col] = tokenSB.nextToken();
					col++;
				}
				
				if (lineMatrixSC[1].equals("0")||lineMatrixSC[1].equals("16") ||lineMatrixSB[1].equals("0")||lineMatrixSB[1].equals("16"))
				{
					
					if (lineMatrixSC[1].equals("0")||lineMatrixSC[1].equals("16"))
					{
						if(lineMatrixSB[1].equals("0")||lineMatrixSB[1].equals("16"))
						{
							//map to both genomes
							outFileSCSB.print (lineMatrixSC[0]+"\t");
							outFileSBSC.print (lineMatrixSB[0]+"\t");
							outFileSC.print (lineMatrixSC[0]+"\t");
							outFileSB.print (lineMatrixSB[0]+"\t");
						
							outFileSCSB.print (lineMatrixSC[1]+"\t");
							outFileSBSC.print (lineMatrixSB[1]+"\t");
							outFileSC.print ("4"+"\t");
							outFileSB.print ("4"+"\t");
						
							for (int j=2; j<11; j++) //bowtie optional fields
							{
								outFileSCSB.print (lineMatrixSC[j]+"\t");
								outFileSBSC.print (lineMatrixSB[j]+"\t");
							}
							outFileSCSB.print (lineMatrixSC[11]);
							outFileSBSC.print (lineMatrixSB[11]);
						
							//need to replace unique.sam outputs with blank fields 
							outFileSC.print ("*"+"\t");
							outFileSB.print ("*"+"\t");
							outFileSC.print ("0"+"\t");
							outFileSB.print ("0"+"\t");
							outFileSC.print ("0"+"\t");
							outFileSB.print ("0"+"\t");
							outFileSC.print ("*"+"\t");
							outFileSB.print ("*"+"\t");
							for (int j=6; j<11; j++)
							{
								outFileSC.print (lineMatrixSC[j]+"\t");
								outFileSB.print (lineMatrixSB[j]+"\t");
							}
							outFileSC.print (lineMatrixSC[11]);
							outFileSB.print (lineMatrixSB[11]);
						
							outFileSCSB.println ();
							outFileSBSC.println ();
							outFileSC.println ();
							outFileSB.println ();
						}
				
						else
						{
							//map only to SC
							outFileSCSB.print (lineMatrixSC[0]+"\t");
							outFileSBSC.print (lineMatrixSB[0]+"\t");
							outFileSC.print (lineMatrixSC[0]+"\t");
							outFileSB.print (lineMatrixSB[0]+"\t");
							
							outFileSCSB.print ("4"+"\t");
							outFileSBSC.print (lineMatrixSB[1]+"\t");
							outFileSC.print (lineMatrixSC[1]+"\t");
							outFileSB.print (lineMatrixSB[1]+"\t");
							
							for (int j=2; j<11; j++)
							{
								outFileSBSC.print (lineMatrixSB[j]+"\t");
								outFileSC.print (lineMatrixSC[j]+"\t");
								outFileSB.print (lineMatrixSB[j]+"\t");
							}
							outFileSBSC.print (lineMatrixSB[11]);
							outFileSC.print (lineMatrixSC[11]);
							outFileSB.print (lineMatrixSB[11]);
							
							//for (int j=13; j<15; j++)
								//outFileSC.print (lineMatrixSC[j]+"\t");
							
							
							//need to replace SCSB.sam output with blank fields 
							outFileSCSB.print ("*"+"\t");
							outFileSCSB.print ("0"+"\t");
							outFileSCSB.print ("0"+"\t");
							outFileSCSB.print ("*"+"\t");
							for (int j=6; j<11; j++)
								outFileSCSB.print (lineMatrixSC[j]+"\t");
							outFileSCSB.print (lineMatrixSC[11]);
														
							outFileSCSB.println ();
							outFileSBSC.println ();
							outFileSC.println ();
							outFileSB.println ();
						}
					}
				
					if ((lineMatrixSB[1].equals("0")||lineMatrixSB[1].equals("16"))&& !(lineMatrixSC[1].equals("0")||lineMatrixSC[1].equals("16")))
					{
						//map to SB only
						outFileSCSB.print (lineMatrixSC[0]+"\t");
						outFileSBSC.print (lineMatrixSB[0]+"\t");
						outFileSC.print (lineMatrixSC[0]+"\t");
						outFileSB.print (lineMatrixSB[0]+"\t");
						
						outFileSCSB.print (lineMatrixSC[1]+"\t");
						outFileSBSC.print ("4"+"\t");
						outFileSC.print (lineMatrixSC[1]+"\t");
						outFileSB.print (lineMatrixSB[1]+"\t");
						
						for (int j=2; j<11; j++)
						{
							outFileSCSB.print (lineMatrixSC[j]+"\t");
							outFileSC.print (lineMatrixSC[j]+"\t");
							outFileSB.print (lineMatrixSB[j]+"\t");
						}
						outFileSCSB.print (lineMatrixSC[11]);
						outFileSC.print (lineMatrixSC[11]);
						outFileSB.print (lineMatrixSB[11]);
						//for (int j=13; j<15; j++)
						//		outFileSB.print (lineMatrixSB[j]+"\t");
						
						//need to replace SBSC.sam output with blank fields 
						outFileSBSC.print ("*"+"\t");
						outFileSBSC.print ("0"+"\t");
						outFileSBSC.print ("0"+"\t");
						outFileSBSC.print ("*"+"\t");
						for (int j=6; j<11; j++)
							outFileSBSC.print (lineMatrixSB[j]+"\t");
						outFileSBSC.print (lineMatrixSB[11]);
						
						outFileSCSB.println ();
						outFileSBSC.println ();
						outFileSC.println ();
						outFileSB.println ();
					}
				}
				else
				{
					//don't map to either
					for (int j=0; j<11; j++)
					{
						outFileSCSB.print (lineMatrixSC[j]+"\t");
						outFileSBSC.print (lineMatrixSB[j]+"\t");
						outFileSC.print (lineMatrixSC[j]+"\t");
						outFileSB.print (lineMatrixSB[j]+"\t");
					}
					outFileSCSB.print (lineMatrixSC[11]);
					outFileSBSC.print (lineMatrixSB[11]);
					outFileSC.print (lineMatrixSC[11]);
					outFileSB.print (lineMatrixSB[11]);
					outFileSCSB.println ();
					outFileSBSC.println ();
					outFileSC.println ();
					outFileSB.println ();
				}	
								
			StringLineSC = bFReaderSC.readLine();
			StringLineSB = bFReaderSB.readLine();
			}
			bFReaderSC.close() ;
			outFileSC.close();
			outFileSCSB.close();
			bFReaderSB.close() ;
			outFileSB.close();
			outFileSBSC.close();
		}		
		catch (FileNotFoundException exception) 
		{
			System.out.println("Can't find file: "+fileNameInSC);
		}
		catch (IOException exception) 
		{
			System.out.println("Reading exception");
		}
				
		return "hello";
	}
	
	
	
	public static void main (String[] args)//test harness
	{
		String fileNamegenomeS = args [0];	
		String fileNamegenomeB = args [1];
		//String fileNamegenomeS = "genomeSU.sam";	
		//String fileNamegenomeB = "genomeB.sam";	
		Split testLoaderObject = new Split();
		String testDataFromFile = testLoaderObject.getDataFromFile(fileNamegenomeS, fileNamegenomeB);	
		System.out.println("Job completed");	
	}
}


