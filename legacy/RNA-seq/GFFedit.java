/*
 *  GFFedit.java
 * 
 *  This program takes a GFF file and edits it, by changing gene names
 *  to the geneID (if they are not of the DDB_G0...format).
 *
 * It outputs the edited GFF file.
 *
 * Author: leo zeef
 * Created: 22/06/2011 13:19:18
 */
import java.io.*;//file input
import java.util.*;	//StringTokenizer

class GFFedit
{
	private String fileNameIn= "";
	private BufferedReader bFReader =null;
	private StringTokenizer token1;
	private String [] lineMatrix;
	int col = 0;
	int totalCount=0;
	//boolean no_errors=true;
		
	//constructor
	public GFFedit()
	{
	}
	
	//make string matrix from the data in the file
	 public String getDataFromFile(String fileNameIn)
	{
		fileNameIn = fileNameIn;
	
		try
		{
		
						
			//make things to read file, count things and to write 1 file.
			FileWriter fw = new FileWriter ("GFFedit_"+fileNameIn);
	      	BufferedWriter bw = new BufferedWriter (fw);
			PrintWriter outFile = new PrintWriter (bw);
			String [] chrTable = new String [9];
			for (int i=0; i<chrTable.length; i++)
				chrTable[i]="";
				
			bFReader = new BufferedReader (new FileReader (fileNameIn));	
			String StringLine = bFReader.readLine();
			//record chr names
				while (StringLine.substring(0,1).equals("#"))
				{
					outFile.print (StringLine);				
					outFile.println ();
					StringLine = bFReader.readLine();
				}
				
			String temp1="";
			String temp2="";
			String temp3="";
			
			while (StringLine != null)
			{		
				token1 = new StringTokenizer (StringLine, "\t");				
				while (token1.hasMoreTokens())
				{
					//System.out.println(row+", "+col);					
					chrTable[col] = token1.nextToken();
					//System.out.println(allFileContentsMatrix [row][col]);
					col++;
				}
				//row++;
				col = 0;
				if (chrTable[2].equals("gene"))
				{
					token1 = new StringTokenizer (chrTable[8], ";");
					temp1=token1.nextToken();
					temp2=token1.nextToken();
					while (token1.hasMoreTokens())
					temp3=token1.nextToken();
					if (temp2.length() <11)
					{
						temp2="Name="+temp1.substring(3,temp1.length());
						chrTable[8]=temp1+";"+temp2+";"+temp3;
						for (int i=0; i<chrTable.length; i++)
						outFile.print (chrTable[i]+"\t");				
						outFile.println ();
					}
					else 
					{					
					if (!temp2.substring(5,11).equals("DDB_G0"))	
					{
						System.out.println("caught "+temp2);
						temp2="Name="+temp1.substring(3,temp1.length());
						chrTable[8]=temp1+";"+temp2+";"+temp3;
						for (int i=0; i<chrTable.length; i++)
						outFile.print (chrTable[i]+"\t");				
						outFile.println ();
						//System.out.println("caught "+);
					}
					else
					{
						outFile.print (StringLine);				
						outFile.println ();
					}
					}
					
				}
				else
				{
					outFile.print (StringLine);				
					outFile.println ();
				}
				temp1="";
				temp2="";
				temp3="";
				
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
			System.out.println("No GFF file specified. To run use: java GFFedit myfile.gff");
			no_errors = false;
		}
		//String fileName = "myfile.gff";	
		GFFedit testLoaderObject = new GFFedit();
		String testDataFromFile = testLoaderObject.getDataFromFile(fileName);	
		
		//if (no_errors)
		//	System.out.println("Job completed");	
	}
}


