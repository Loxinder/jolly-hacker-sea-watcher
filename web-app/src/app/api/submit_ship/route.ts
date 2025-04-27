import { NextResponse } from 'next/server';

// Handle OPTIONS request for CORS preflight
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}

export async function POST(request: Request) {
  try {
    // Parse the incoming request body
    const body = await request.json();
    
    // Log request for debugging
    console.log('API route received request:', body);
    
    // Forward to the external API
    const response = await fetch('https://natsec.crowdwise.bio/submit_ship', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    
    // Check if the request was successful
    if (!response.ok) {
      const errorText = await response.text();
      console.error('External API error:', response.status, errorText);
      return NextResponse.json(
        { error: `API request failed with status ${response.status}` }, 
        { status: response.status }
      );
    }
    
    // Parse and return the response
    const data = await response.json();
    console.log('API route forwarded response:', data);
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in API route handler:', error);
    return NextResponse.json(
      { error: 'Failed to process request' }, 
      { status: 500 }
    );
  }
} 