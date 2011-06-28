/*
//this program takes a SAM file and reports mapping statistics.
It produces 1 file:
sam file headers
chr1	reads	approx_length
...
chrN	reads	approx_length
Total reads
Total uniquely mapped reads

to run e.g. qsub -q solid.q -b y -cwd -V -N test1 'java SamStats BY4741xNCYC2669_pooledUCSCv0_1000.sam'


/*
 * Author: leo zeef
 * Created: 22/06/2011 13:19:18
 */
import java.io.*;//file input
import java.util.*;	//StringTokenizer

class SamStats
{
	private String fileNameIn= "";
	private BufferedReader bFReader =null;
	private StringTokenizer token;
	private String [] lineMatrix;
	int col = 0;
	int totalCount=0;
	//boolean no_errors=true;
		
	//constructor
	public SamStats()
	{
	}
	
	//make string matrix from the data in the file
	 public String getDataFromFile(String fileNameIn)
	{
		fileNameIn = fileNameIn;
	
		try
		{
			//make things to read file count chromosomes			
			int k=0;
			bFReader = new BufferedReader (new FileReader (fileNameIn));	
			String StringLine = bFReader.readLine();
			String s = "";
			
			//how many chromosomes?	
			while (StringLine.substring(0,1).equals("@"))
			{
				if (StringLine.substring(1,3).equals("SQ"))
					k++;
				StringLine = bFReader.readLine();
			}
						
			//make things to read file, count things and to write 1 file.
			FileWriter fw = new FileWriter ("SamStats_maponly_"+fileNameIn+".stats");
	      	BufferedWriter bw = new BufferedWriter (fw);
			PrintWriter outFile = new PrintWriter (bw);
			String chrS = "Chr-";
			String chrLength = "Length";
			int chrCount = 0;
			int mappedCount =0;
			totalCount=0;
			s = "";			
			int [] countsTable = new int [k];			
			for (int i=0; i<countsTable.length; i++)
				countsTable[i]=0;
			String [] chrTable = new String [k];
			k=0;
			for (int i=0; i<chrTable.length; i++)
				chrTable[i]="";
				
			bFReader = new BufferedReader (new FileReader (fileNameIn));	
			StringLine = bFReader.readLine();
			//record chr names
				while (StringLine.substring(0,1).equals("@"))
				{
					token = new StringTokenizer (StringLine, "\t");
					if (StringLine.substring(1,3).equals("SQ"))
					{
						s= token.nextToken();
						s= token.nextToken();
						chrTable[k]=s.substring(3,(s.length()));
						//System.out.println(chrTable[k]);
						k++;
					}
					
					StringLine = bFReader.readLine();
				}
			while (StringLine != null)
			{				
				if (!StringLine.substring(0,1).equals("@"))
				{	
					totalCount++;			
					//outFile.println ();									
					//headers of the files are now done. Now deal with tab delimited data.
					token = new StringTokenizer (StringLine, "\t");
					lineMatrix = new String [15];									
					col = 0;
					
					while (token.hasMoreTokens())
					{
						//System.out.println("test");					
						lineMatrix[col] = token.nextToken();
						col++;
					}
					
					
					if (!lineMatrix[2].equals("*"))
					{
						mappedCount++;
						for (int i=0; i<chrTable.length; i++)
						{
							if (lineMatrix[2].equals(chrTable[i]))
							{
								countsTable[i]++;
								//chrLength=lineMatrix[3];
							}
						}
					}					
				}
				
				StringLine = bFReader.readLine();
			}
			//print results file
			outFile.print ("Reads mapped to each chromosome/contig (only uniquely mapped are considered):");
			outFile.println ();
			outFile.print ("Chr."+"\t");
			outFile.print ("Reads"+"\t");
			outFile.print ("Percentage"+"\t");
			outFile.println ();
			for (int i=0; i<chrTable.length; i++)
			{
				outFile.print (chrTable[i]+"\t");
				outFile.print (countsTable[i]+"\t");
				outFile.print ((countsTable[i]*100)/mappedCount+"%"+"\t");
				outFile.println ();
			}
	
			outFile.println ();
			outFile.print ("Total uniquely mapped reads = "+mappedCount);
			outFile.println ();
			outFile.print ("Total reads in the sample = "+totalCount);
			outFile.println ();
						
			outFile.println ();
			outFile.print ("sam file header:");
			outFile.println ();			
		
			bFReader = new BufferedReader (new FileReader (fileNameIn));	
			StringLine = bFReader.readLine();
			//print headers
			k=0;
				while (StringLine.substring(0,1).equals("@"))
				{
					outFile.print (StringLine);	
					outFile.println ();
					token = new StringTokenizer (StringLine, "\t");
					if (StringLine.substring(1,3).equals("SQ"))
					{
						s= token.nextToken();
						s= token.nextToken();
						chrTable[k]=s.substring(3,(s.length()));
						//System.out.println(chrTable[k]);
						k++;
					}
					
					StringLine = bFReader.readLine();
				}
			
			bFReader.close() ;
			outFile.close();
		}
				
		catch (FileNotFoundException exception) 
		{
			System.out.println("Can't find file: "+fileNameIn);
		}
		catch (IOException exception) 
		{
			System.out.println("Reading exception");
		}
				
		return "hello";
	}
	
	
	
	public static void main (String[] args)//test harness
	{
		boolean no_errors=true;
		String fileName="";
		try{
			fileName = args [0];
		}
		catch (ArrayIndexOutOfBoundsException exception) 
		{
			System.out.println("No sam file specified. To run use: java SamStats myfile.sam");
			no_errors = false;
		}	
		//String fileName = "BY4741xNCYC2669_pooledUCSCv0_1000.sam";	
		SamStats testLoaderObject = new SamStats();
		String testDataFromFile = testLoaderObject.getDataFromFile(fileName);	
		
		if (no_errors)
			System.out.println("Job completed");	
	}
}


